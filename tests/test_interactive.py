#!/usr/bin/env python3
"""
Interactive agent testing - command-line interface for real-time testing.
"""

import sys
import os
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from leocode.config import Config
from leocode.client import RouterClient
from leocode.agent import AgentTools
import json


class InteractiveAgentTester:
    """Interactive command-line agent tester."""
    
    def __init__(self, working_dir: str = "/tmp"):
        self.config = Config.load()
        self.client = RouterClient(self.config)
        self.agent = AgentTools(working_dir)
        self.working_dir = working_dir
        self.messages = []
        self.use_tools = True
    
    def print_banner(self):
        """Print welcome banner."""
        print("\n╔" + "═" * 68 + "╗")
        print("║" + " " * 18 + "LEOCODE INTERACTIVE AGENT TESTER" + " " * 18 + "║")
        print("╚" + "═" * 68 + "╝\n")
        print(f"Endpoint: {self.config.base_url}")
        print(f"Model: {self.config.model}")
        print(f"Working Dir: {self.working_dir}")
        print(f"Tools: {'Enabled' if self.use_tools else 'Disabled'}")
        print("\nCommands:")
        print("  /help     - Show this help")
        print("  /tools    - Toggle tool calling")
        print("  /clear    - Clear conversation")
        print("  /exit     - Exit tester")
        print("  /info     - Show session info")
        print("  /save     - Save conversation")
        print("\nType your message and press Enter...\n")
    
    async def send_message(self, user_input: str) -> str:
        """Send message to agent and get response."""
        self.messages.append({"role": "user", "content": user_input})
        
        messages = [{"role": "system", "content": self.config.system_prompt}]
        messages.extend(self.messages)
        
        tools = self.agent.tool_definitions if self.use_tools else None
        
        print("\n" + "─" * 70)
        print("AGENT RESPONSE:")
        print("─" * 70)
        
        response_parts = []
        
        try:
            if tools:
                # With tools
                stream = await self.client.client.chat.completions.create(
                    model=self.config.model,
                    messages=messages,
                    tools=tools,
                    temperature=0.3,
                    max_tokens=2000,
                    stream=True,
                )
                
                tool_calls = {}
                async for chunk in stream:
                    delta = chunk.choices[0].delta if chunk.choices else None
                    if not delta:
                        continue
                    
                    if delta.content:
                        response_parts.append(delta.content)
                        print(delta.content, end="", flush=True)
                    
                    if delta.tool_calls:
                        for tc in delta.tool_calls:
                            idx = tc.index
                            if idx not in tool_calls:
                                tool_calls[idx] = {"id": "", "name": "", "arguments": ""}
                            if tc.id:
                                tool_calls[idx]["id"] = tc.id
                            if tc.function:
                                if tc.function.name:
                                    tool_calls[idx]["name"] = tc.function.name
                                if tc.function.arguments:
                                    tool_calls[idx]["arguments"] += tc.function.arguments
                
                # Execute tool calls
                if tool_calls:
                    print("\n\n" + "┌" + "─" * 68 + "┐")
                    print("│" + " " * 25 + "TOOL EXECUTION" + " " * 29 + "│")
                    print("└" + "─" * 68 + "┘")
                    
                    for idx in sorted(tool_calls.keys()):
                        tc = tool_calls[idx]
                        name = tc["name"]
                        try:
                            args = json.loads(tc["arguments"]) if tc["arguments"] else {}
                        except json.JSONDecodeError:
                            args = {}
                        
                        print(f"\n▶ Tool: {name}")
                        print(f"  Args: {json.dumps(args, indent=8)}")
                        
                        result = self.agent.execute(name, args)
                        print(f"  Result: {result[:300]}{'...' if len(result) > 300 else ''}")
                        
                        response_parts.append(f"\n\n[Tool: {name}]\n{result[:500]}")
                        
                        messages.append({
                            "role": "assistant",
                            "content": None,
                            "tool_calls": [{
                                "id": tc["id"],
                                "type": "function",
                                "function": {"name": name, "arguments": tc["arguments"]},
                            }],
                        })
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tc["id"],
                            "content": result[:5000],
                        })
                    
                    # Follow-up response
                    print("\n" + "─" * 70)
                    print("FOLLOW-UP:")
                    print("─" * 70)
                    
                    stream2 = await self.client.client.chat.completions.create(
                        model=self.config.model,
                        messages=messages,
                        temperature=0.3,
                        max_tokens=1000,
                        stream=True,
                    )
                    
                    async for chunk in stream2:
                        delta = chunk.choices[0].delta if chunk.choices else None
                        if delta and delta.content:
                            response_parts.append(delta.content)
                            print(delta.content, end="", flush=True)
                
                print()
            else:
                # Without tools
                response = await self.client.chat_sync(messages, model=self.config.model)
                response_parts.append(response)
                print(response)
            
            full_response = "".join(response_parts)
            self.messages.append({"role": "assistant", "content": full_response})
            
            print("─" * 70 + "\n")
            
            return full_response
            
        except Exception as e:
            error_msg = f"Error: {e}"
            print(f"\n✗ {error_msg}\n")
            return error_msg
    
    async def run(self):
        """Run interactive loop."""
        self.print_banner()
        
        while True:
            try:
                # Get user input
                user_input = input("You: ").strip()
                
                if not user_input:
                    continue
                
                # Handle commands
                if user_input.startswith("/"):
                    if user_input == "/exit":
                        print("\nGoodbye!\n")
                        break
                    elif user_input == "/help":
                        self.print_banner()
                    elif user_input == "/tools":
                        self.use_tools = not self.use_tools
                        print(f"\n✓ Tools {'enabled' if self.use_tools else 'disabled'}\n")
                    elif user_input == "/clear":
                        self.messages = []
                        print("\n✓ Conversation cleared\n")
                    elif user_input == "/info":
                        print(f"\nSession Info:")
                        print(f"  Messages: {len(self.messages)}")
                        print(f"  Tools: {'Enabled' if self.use_tools else 'Disabled'}")
                        print(f"  Model: {self.config.model}")
                        print(f"  Working Dir: {self.working_dir}\n")
                    elif user_input == "/save":
                        filename = f"test_session_{len(self.messages)}.json"
                        Path(filename).write_text(json.dumps(self.messages, indent=2))
                        print(f"\n✓ Saved to {filename}\n")
                    else:
                        print(f"\n✗ Unknown command: {user_input}\n")
                    continue
                
                # Send message to agent
                await self.send_message(user_input)
                
            except KeyboardInterrupt:
                print("\n\nUse /exit to quit\n")
            except EOFError:
                print("\n\nGoodbye!\n")
                break


async def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Interactive Agent Tester")
    parser.add_argument(
        "-d", "--dir",
        default="/tmp",
        help="Working directory for agent",
    )
    
    args = parser.parse_args()
    
    tester = InteractiveAgentTester(working_dir=args.dir)
    await tester.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nInterrupted.\n")
        sys.exit(130)
