"""
LeoCode TUI Backend
Headless agent loop that communicates with the TypeScript frontend via IPC.
"""

import json
import sys
import asyncio
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from leocode.ui.ipc_server import get_ipc_server
from leocode.config import Config
from leocode.client import RouterClient
from leocode.executor import ToolExecutor
from leocode.events import EventBus
from leocode.permissions import PermissionEngine
from leocode.tools.registry import ToolRegistry
from leocode.tools.filesystem import register_filesystem_tools
from leocode.tools.search_tools import register_search_tools
from leocode.tools.execution import register_execution_tools
from leocode.tools.agent_tools import register_agent_tools
from leocode.tools.web import register_web_tools
from leocode.tools.code_intel import register_code_intel_tools
from leocode.tools.extensibility import register_extensibility_tools


class TUIAgent:
    def __init__(self, working_dir: str):
        self.working_dir = working_dir
        self.config = Config.load()
        self.client = RouterClient(self.config)
        self.tool_registry = ToolRegistry()
        self.events = EventBus()
        self.permissions = PermissionEngine(self.config.permission_policy)
        self.tool_executor = ToolExecutor(
            registry=self.tool_registry,
            permissions=self.permissions,
            events=self.events,
            approval_callback=self._handle_approval,
        )
        self.server = get_ipc_server()
        self.messages: list[dict] = []
        self._cancelled = False
        self._approval_future = None
        self.mode = "code"  # "code" or "plan"
        self._register_tools()

    def _register_tools(self):
        register_filesystem_tools(self.tool_registry, self.working_dir)
        register_search_tools(self.tool_registry, self.working_dir)
        register_execution_tools(self.tool_registry, self.working_dir)
        register_agent_tools(self.tool_registry, self.working_dir)
        register_web_tools(self.tool_registry, self.working_dir)
        register_code_intel_tools(self.tool_registry, self.working_dir)
        register_extensibility_tools(self.tool_registry, self.working_dir)

    async def _handle_approval(self, meta, arguments, tool_name) -> str:
        sent = await self.server.send("permission_requested", {
            "id": f"perm-{tool_name}",
            "tool_name": tool_name,
            "description": f"Execute {tool_name}",
            "params": arguments,
            "risk": meta.risk_level.value if hasattr(meta.risk_level, 'value') else str(meta.risk_level),
        })
        if not sent:
            return "denied"
        loop = asyncio.get_event_loop()
        future = loop.create_future()
        self._approval_future = future
        try:
            return await asyncio.wait_for(future, timeout=120.0)
        except asyncio.TimeoutError:
            return "denied"

    async def handle_user_message(self, params: dict) -> dict:
        import datetime
        def _debug(msg):
            try:
                with open("/tmp/leocode-backend-debug.log", "a") as f:
                    f.write(f"[AGENT {datetime.datetime.now().isoformat()}] {msg}\n")
            except Exception:
                pass

        content = params.get("content", "").strip()
        _debug(f"handle_user_message called: content='{content[:80]}'")
        if not content:
            return {"error": "Empty message"}

        self._cancelled = False
        self.messages.append({"role": "user", "content": content})
        _debug(f"Messages count: {len(self.messages)}")

        # Build system prompt based on mode
        if self.mode == "plan":
            mode_instruction = "\n\nYou are in PLAN mode. Focus on planning and design. Explain your approach, break down the problem, and outline steps WITHOUT executing tools or writing code. Be thorough in your reasoning."
        else:
            mode_instruction = "\n\nYou are in CODE mode (default). Execute tools, write code, and make changes as needed to complete the user's request."

        full_messages = [
            {"role": "system", "content": self.config.system_prompt + mode_instruction}
        ] + self.messages[-40:]

        await self.server.send("agent_state_changed", {"status": "thinking", "is_streaming": True})
        _debug("Sent agent_state_changed thinking")

        tools = self.tool_registry.get_openai_tools()
        max_rounds = 10
        full_response = ""
        thinking_accum = ""
        in_thinking = False

        try:
            _debug(f"Starting chat_stream with model={self.config.model}")
            for round_num in range(max_rounds):
                if self._cancelled:
                    _debug("Cancelled before chat_stream")
                    break

                tool_calls_data = {}

                async for chunk in self.client.chat_stream(
                    messages=full_messages,
                    model=self.config.model,
                    tools=tools if tools else None,
                ):
                    if self._cancelled:
                        break

                    if chunk.content:
                        full_response += chunk.content

                        # Detect thinking tags in accumulated content
                        if '<thinking>' in full_response and not in_thinking:
                            in_thinking = True
                            after_tag = full_response[full_response.index('<thinking>') + len('<thinking>'):]
                            thinking_accum = after_tag
                            await self.server.send("thinking_stream", {
                                "content": thinking_accum,
                            })
                        elif in_thinking:
                            if '</thinking>' in full_response:
                                end_idx = full_response.index('</thinking>')
                                start_idx = full_response.index('<thinking>') + len('<thinking>')
                                thinking_accum = full_response[start_idx:end_idx].strip()
                                in_thinking = False
                                await self.server.send("thinking_stream", {
                                    "content": thinking_accum,
                                    "done": True,
                                })
                            else:
                                start_idx = full_response.index('<thinking>') + len('<thinking>')
                                thinking_accum = full_response[start_idx:]
                                await self.server.send("thinking_stream", {
                                    "content": thinking_accum,
                                })

                        await self.server.send("assistant_stream", {
                            "content": chunk.content,
                            "accumulated": full_response,
                        })

                    for tc in chunk.tool_calls:
                        idx = tc.index
                        if idx not in tool_calls_data:
                            tool_calls_data[idx] = {"id": tc.id, "name": tc.name, "arguments": ""}
                        if tc.id:
                            tool_calls_data[idx]["id"] = tc.id
                        if tc.name:
                            tool_calls_data[idx]["name"] = tc.name
                        if tc.arguments:
                            tool_calls_data[idx]["arguments"] += tc.arguments

                if self._cancelled:
                    break

                if tool_calls_data:
                    assistant_msg = {
                        "role": "assistant",
                        "content": full_response if full_response else None,
                        "tool_calls": [
                            {
                                "id": tc["id"],
                                "type": "function",
                                "function": {"name": tc["name"], "arguments": tc["arguments"]},
                            }
                            for tc in tool_calls_data.values()
                        ]
                    }
                    full_messages.append(assistant_msg)
                    self.messages.append(assistant_msg)

                    for tc in tool_calls_data.values():
                        if self._cancelled:
                            break

                        tool_name = tc["name"]
                        try:
                            args = json.loads(tc["arguments"]) if tc["arguments"] else {}
                        except json.JSONDecodeError:
                            args = {}

                        await self.server.send("tool_use", {
                            "id": tc["id"], "name": tool_name,
                            "input": args, "state": "running",
                        })

                        await self.server.send("agent_state_changed", {"status": "tool_use", "is_streaming": True})
                        result = await self.tool_executor.execute(tool_name, args)

                        await self.server.send("tool_result", {
                            "id": tc["id"], "name": tool_name,
                            "result": result[:10000],
                            "state": "success" if not result.startswith("Error") else "error",
                        })

                        tool_msg = {"role": "tool", "tool_call_id": tc["id"], "content": result[:10000]}
                        full_messages.append(tool_msg)
                        self.messages.append(tool_msg)

                    full_response = ""
                    continue
                else:
                    break

            _debug(f"chat_stream completed: full_response len={len(full_response)} tool_calls_data keys={list(tool_calls_data.keys())}")

            if full_response:
                thinking = ""
                response = full_response
                if "<thinking>" in full_response and "</thinking>" in full_response:
                    start = full_response.index("<thinking>") + len("<thinking>")
                    end = full_response.index("</thinking>")
                    thinking = full_response[start:end].strip()
                    response = full_response[:full_response.index("<thinking>")].strip() + \
                              full_response[end + len("</thinking>"):].strip()

                await self.server.send("assistant_message", {
                    "content": response, "thinking": thinking, "streaming": False,
                })
                self.messages.append({"role": "assistant", "content": response})

            await self.server.send("agent_state_changed", {"status": "idle", "is_streaming": False})
            return {"status": "ok"}

        except Exception as e:
            _debug(f"ERROR in handle_user_message: {type(e).__name__}: {e}")
            await self.server.send("error", {"message": str(e)})
            await self.server.send("agent_state_changed", {"status": "idle", "is_streaming": False})
            return {"error": str(e)}

    async def handle_interrupt(self, params: dict) -> None:
        self._cancelled = True
        self.tool_executor.cancel_all()
        await self.server.send("agent_state_changed", {"status": "idle", "is_streaming": False})

    async def handle_permission_response(self, params: dict) -> dict:
        action = params.get("action", "denied")
        if self._approval_future and not self._approval_future.done():
            if action == "allow":
                self._approval_future.set_result("allow_once")
            elif action == "always_allow":
                self._approval_future.set_result("always_allow")
            else:
                self._approval_future.set_result("denied")
        return {"status": "ok"}

    async def handle_get_models(self, params: dict) -> dict:
        try:
            models = await self.client.list_models()
        except Exception:
            models = []
        if not models:
            models = [{"id": self.config.model, "owned_by": ""}]
        return {"models": [m["id"] for m in models]}

    async def handle_switch_model(self, params: dict) -> dict:
        model = params.get("model", "")
        if model:
            self.config.model = model
            self.config.save()
            self.client.reconnect()
        return {"status": "ok", "model": self.config.model}

    async def handle_clear(self, params: dict) -> dict:
        self.messages = []
        return {"status": "ok"}

    async def handle_list_sessions(self, params: dict) -> dict:
        """List saved conversation sessions."""
        from leocode.config import CONVERSATIONS_DIR
        import json
        
        sessions = []
        if CONVERSATIONS_DIR.exists():
            for f in sorted(CONVERSATIONS_DIR.glob("*.json"), reverse=True)[:40]:
                try:
                    data = json.loads(f.read_text())
                    sessions.append({
                        "id": f.stem,
                        "title": data.get("title", f.stem),
                        "timestamp": data.get("timestamp", ""),
                    })
                except Exception:
                    continue
        return {"status": "ok", "sessions": sessions}

    async def handle_load_session(self, params: dict) -> dict:
        """Load a saved conversation session."""
        from leocode.config import CONVERSATIONS_DIR
        import json
        
        session_id = params.get("session_id", "")
        if not session_id:
            return {"error": "No session_id provided"}
        
        session_file = CONVERSATIONS_DIR / f"{session_id}.json"
        if not session_file.exists():
            return {"error": f"Session not found: {session_id}"}
        
        try:
            data = json.loads(session_file.read_text())
            messages = data.get("messages", [])
            # Filter to only user/assistant messages (skip system/tool messages that might break the flow)
            filtered_messages = [
                msg for msg in messages 
                if msg.get("role") in ["user", "assistant"]
            ]
            self.messages = filtered_messages
            return {
                "status": "ok",
                "messages": filtered_messages,
                "title": data.get("title", session_id),
            }
        except Exception as e:
            return {"error": f"Failed to load session: {str(e)}"}

    async def handle_toggle_mode(self, params: dict) -> dict:
        """Toggle between plan and code mode."""
        target_mode = params.get("mode", "")
        if target_mode in ["plan", "code"]:
            self.mode = target_mode
        else:
            # Toggle if no specific mode provided
            self.mode = "plan" if self.mode == "code" else "code"
        
        await self.server.send("agent_state_changed", {
            "status": "idle",
            "mode": self.mode,
        })
        
        return {"status": "ok", "mode": self.mode}

    async def handle_compact_conversation(self, params: dict) -> dict:
        """Compact the conversation by generating a summary."""
        if len(self.messages) == 0:
            return {"error": "No messages to compact"}
        
        # Build a prompt to summarize the conversation
        summary_messages = [
            {
                "role": "system",
                "content": "You are a conversation summarizer. Generate a concise but comprehensive summary of the following conversation, preserving all important context, decisions, and code changes. The summary will replace the full conversation history."
            },
            {
                "role": "user",
                "content": f"Please summarize this conversation:\n\n{json.dumps(self.messages, indent=2)}"
            }
        ]
        
        try:
            # Get summary from the model (non-streaming for simplicity)
            summary_text = ""
            async for chunk in self.client.chat_stream(
                messages=summary_messages,
                model=self.config.model,
                tools=None,
            ):
                if chunk.content:
                    summary_text += chunk.content
            
            if not summary_text:
                return {"error": "Failed to generate summary"}
            
            # Replace messages with a single system message containing the summary
            self.messages = [{
                "role": "system",
                "content": f"[Conversation Summary]\n\n{summary_text.strip()}"
            }]
            
            return {
                "status": "ok",
                "summary": summary_text.strip(),
                "message_count": len(self.messages)
            }
        except Exception as e:
            return {"error": f"Compaction failed: {str(e)}"}


async def main():
    import datetime
    def _debug(msg):
        try:
            with open("/tmp/leocode-backend-debug.log", "a") as f:
                f.write(f"[STARTUP {datetime.datetime.now().isoformat()}] {msg}\n")
        except Exception:
            pass

    working_dir = os.getcwd()
    _debug(f"main() starting: working_dir={working_dir}")

    server = get_ipc_server()
    server.setup()
    _debug(f"Server setup done: socket_path={server.socket_path}")

    agent = TUIAgent(working_dir)
    _debug(f"Agent created: model={agent.config.model}")

    server.register("user_message", agent.handle_user_message)
    server.register("interrupt", agent.handle_interrupt)
    server.register("permission_response", agent.handle_permission_response)
    server.register("get_models", agent.handle_get_models)
    server.register("switch_model", agent.handle_switch_model)
    server.register("clear", agent.handle_clear)
    server.register("list_sessions", agent.handle_list_sessions)
    server.register("load_session", agent.handle_load_session)
    server.register("toggle_mode", agent.handle_toggle_mode)
    server.register("compact_conversation", agent.handle_compact_conversation)
    _debug("All handlers registered")

    server.set_ready({"model": agent.config.model, "working_dir": working_dir, "mode": agent.mode})
    _debug("Starting server...")
    await server.start()


if __name__ == "__main__":
    asyncio.run(main())
