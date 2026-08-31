"""Comprehensive tests for the Leocode tool system."""

import asyncio
import json
import os
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from leocode.events import EventBus, Event, EventType
from leocode.permissions import (
    PermissionEngine, PermissionAction, PermissionRule, RiskLevel, DANGEROUS_PATTERNS
)
from leocode.tools.registry import ToolRegistry, ToolMetadata, ToolCategory, ToolSource, RetryPolicy
from leocode.executor import ToolExecutor, ExecutionStatus, ToolExecution
from leocode.todo import TodoManager, TodoTask, TodoStatus, TodoPriority


class Colors:
    PASS = "\033[92m"
    FAIL = "\033[91m"
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"


def log_test(name, passed, detail=""):
    icon = f"{Colors.PASS}✓{Colors.ENDC}" if passed else f"{Colors.FAIL}✗{Colors.ENDC}"
    suffix = f" ({detail})" if detail else ""
    print(f"  {icon} {name}{suffix}")
    return passed


def section(name):
    print(f"\n{Colors.HEADER}{'─' * 60}{Colors.ENDC}")
    print(f"{Colors.BOLD}  {name}{Colors.ENDC}")
    print(f"{Colors.HEADER}{'─' * 60}{Colors.ENDC}")


def run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# ═══════════════════════════════════════════════════════
# Tool Registry Tests
# ═══════════════════════════════════════════════════════

def test_tool_registry():
    section("Tool Registry")
    results = []

    registry = ToolRegistry()
    results.append(log_test("Empty registry", registry.count() == 0))

    meta = ToolMetadata(
        id="test_read",
        name="Test Read",
        description="Read a test file",
        category=ToolCategory.FILESYSTEM,
        input_schema={"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
    )
    registry.register(meta, lambda tid, args: asyncio.coroutine(lambda: "ok")())
    results.append(log_test("Register tool", registry.count() == 1))
    results.append(log_test("Resolve tool", registry.resolve("test_read") is not None))
    results.append(log_test("Tool exists", registry.exists("test_read")))
    results.append(log_test("List all", len(registry.list_all()) == 1))

    # Register more tools
    for i in range(5):
        m = ToolMetadata(
            id=f"tool_{i}",
            name=f"Tool {i}",
            description=f"Tool number {i}",
            category=ToolCategory.SEARCH if i % 2 == 0 else ToolCategory.EXECUTION,
            input_schema={"type": "object", "properties": {}},
        )
        registry.register(m, lambda tid, args: asyncio.coroutine(lambda: "ok")())
    results.append(log_test("Register multiple", registry.count() == 6))

    search_tools = registry.discover(category=ToolCategory.SEARCH)
    results.append(log_test("Discover by category", len(search_tools) == 3))

    # OpenAI schema
    schemas = registry.get_openai_tools()
    results.append(log_test("OpenAI schema", len(schemas) == 6 and schemas[0]["type"] == "function"))

    # Unregister
    registry.unregister("tool_0")
    results.append(log_test("Unregister", registry.count() == 5 and not registry.exists("tool_0")))

    # Source filtering
    registry.register(
        ToolMetadata(id="mcp_tool", name="MCP Tool", description="MCP", category=ToolCategory.MCP, input_schema={}, source=ToolSource.MCP),
        lambda tid, args: asyncio.coroutine(lambda: "mcp")(),
    )
    mcp_tools = registry.get_by_source(ToolSource.MCP)
    results.append(log_test("Source filtering", len(mcp_tools) == 1))

    # Summary
    summary = registry.summary()
    results.append(log_test("Summary generation", "Tools" in summary and "filesystem" in summary))

    return all(results)


# ═══════════════════════════════════════════════════════
# Permission Engine Tests
# ═══════════════════════════════════════════════════════

def test_permission_engine():
    section("Permission Engine")
    results = []

    engine = PermissionEngine(policy="balanced")
    results.append(log_test("Create engine", engine is not None))

    # Safe tools should be allowed
    action = engine.check("read", {"path": "test.py"})
    results.append(log_test("Read → ALLOW", action == PermissionAction.ALLOW))

    action = engine.check("list_dir", {"path": "."})
    results.append(log_test("List_dir → ALLOW", action == PermissionAction.ALLOW))

    action = engine.check("glob", {"pattern": "*.py"})
    results.append(log_test("Glob → ALLOW", action == PermissionAction.ALLOW))

    action = engine.check("grep", {"pattern": "def"})
    results.append(log_test("Grep → ALLOW", action == PermissionAction.ALLOW))

    action = engine.check("todo", {"action": "list"})
    results.append(log_test("Todo → ALLOW", action == PermissionAction.ALLOW))

    # Dangerous tools should need approval
    action = engine.check("shell", {"command": "ls"})
    results.append(log_test("Shell → ASK", action == PermissionAction.ASK))

    action = engine.check("write", {"path": "test.py", "content": "x"})
    results.append(log_test("Write → ASK", action == PermissionAction.ASK))

    action = engine.check("edit", {"path": "test.py", "old": "a", "new": "b"})
    results.append(log_test("Edit → ASK", action == PermissionAction.ASK))

    # Execute should be denied
    action = engine.check("execute", {"workflow": "deploy"})
    results.append(log_test("Execute → DENY", action == PermissionAction.DENY))

    # Risk levels
    results.append(log_test("Read risk = SAFE", engine.get_risk_level("read") == RiskLevel.SAFE))
    results.append(log_test("Shell risk = HIGH", engine.get_risk_level("shell") == RiskLevel.HIGH))
    results.append(log_test("Write risk = MEDIUM", engine.get_risk_level("write") == RiskLevel.MEDIUM))
    results.append(log_test("Execute risk = CRITICAL", engine.get_risk_level("execute") == RiskLevel.CRITICAL))

    # Dangerous command detection
    results.append(log_test("rm -rf / detected", engine.is_command_dangerous("rm -rf /")))
    results.append(log_test("sudo detected", engine.is_command_dangerous("sudo apt install")))
    results.append(log_test("ls not dangerous", not engine.is_command_dangerous("ls -la")))
    results.append(log_test("git not dangerous", not engine.is_command_dangerous("git status")))

    # Allow once
    engine.allow_once("shell", {"command": "echo hello"})
    action = engine.check("shell", {"command": "echo hello"})
    results.append(log_test("Allow once", action == PermissionAction.ALLOW))

    # Deny
    engine.deny("read", {"path": "secret.txt"})
    action = engine.check("read", {"path": "secret.txt"})
    results.append(log_test("Deny overrides", action == PermissionAction.DENY))

    # Permissive policy
    permissive = PermissionEngine(policy="permissive")
    action = permissive.check("read", {"path": "anything"})
    results.append(log_test("Permissive read → ALLOW", action == PermissionAction.ALLOW))

    # Describe action
    desc = engine.describe_action("shell", {"command": "npm test"})
    results.append(log_test("Describe shell", "shell" in desc.lower() or "execute" in desc.lower()))

    desc = engine.describe_action("write", {"path": "src/main.py"})
    results.append(log_test("Describe write", "write" in desc.lower() or "file" in desc.lower()))

    return all(results)


# ═══════════════════════════════════════════════════════
# Event Bus Tests
# ═══════════════════════════════════════════════════════

def test_event_bus():
    section("Event Bus")
    results = []

    bus = EventBus()
    results.append(log_test("Create bus", bus is not None))

    received = []

    async def handler(event: Event):
        received.append(event)

    bus.subscribe(EventType.TOOL_COMPLETED, handler)
    results.append(log_test("Subscribe", len(bus._handlers[EventType.TOOL_COMPLETED]) == 1))

    event = Event(type=EventType.TOOL_COMPLETED, data={"tool": "read"})
    run_async(bus.emit(event))
    results.append(log_test("Emit + receive", len(received) == 1 and received[0].data["tool"] == "read"))

    # Wildcard
    wildcard_received = []
    async def wildcard_handler(event: Event):
        wildcard_received.append(event)

    bus.subscribe_all(wildcard_handler)
    run_async(bus.emit(Event(type=EventType.TOOL_FAILED, data={"error": "oops"})))
    results.append(log_test("Wildcard handler", len(wildcard_received) == 1))

    # Unsubscribe
    bus.unsubscribe(EventType.TOOL_COMPLETED, handler)
    results.append(log_test("Unsubscribe", handler not in bus._handlers.get(EventType.TOOL_COMPLETED, [])))

    # History
    history = bus.get_history(limit=5)
    results.append(log_test("History tracking", len(history) >= 2))

    # Clear
    bus.clear()
    results.append(log_test("Clear", len(bus._handlers) == 0 and len(bus._history) == 0))

    return all(results)


# ═══════════════════════════════════════════════════════
# Todo Manager Tests
# ═══════════════════════════════════════════════════════

def test_todo_manager():
    section("Todo Manager")
    results = []

    mgr = TodoManager()
    results.append(log_test("Create manager", mgr is not None))

    # Create tasks
    t1 = mgr.create("Analyze codebase", active_form="Analyzing codebase", priority="high")
    results.append(log_test("Create task", t1.content == "Analyze codebase" and t1.status == TodoStatus.PENDING))

    t2 = mgr.create("Write tests", priority="medium")
    t3 = mgr.create("Deploy", priority="low")
    results.append(log_test("Create multiple", len(mgr.list_all()) == 3))

    # Get
    task = mgr.get(t1.id)
    results.append(log_test("Get task", task is not None and task.content == "Analyze codebase"))

    # Update
    mgr.update(t1.id, content="Analyze entire codebase")
    results.append(log_test("Update content", mgr.get(t1.id).content == "Analyze entire codebase"))

    # Set in_progress
    mgr.set_status(t1.id, "in_progress")
    active = mgr.active_task()
    results.append(log_test("Active task", active is not None and active.id == t1.id))

    # Complete
    result = mgr.complete(t1.id)
    results.append(log_test("Complete", "Completed" in result and mgr.get(t1.id).status == TodoStatus.COMPLETED))

    # Cancel
    mgr.cancel(t3.id)
    results.append(log_test("Cancel", mgr.get(t3.id).status == TodoStatus.CANCELLED))

    # List by status
    completed = mgr.list_by_status("completed")
    results.append(log_test("List by status", len(completed) == 1))

    # Progress
    progress = mgr.progress()
    results.append(log_test("Progress", progress["completed"] == 1 and progress["total"] == 3))

    # Summary
    summary = mgr.summary()
    results.append(log_test("Summary", "1/3" in summary or "progress" in summary.lower()))

    # Delete
    mgr.delete(t2.id)
    results.append(log_test("Delete", len(mgr.list_all()) == 2))

    # Clear completed
    count = mgr.clear_completed()
    results.append(log_test("Clear completed", count == 1 and len(mgr.list_all()) == 1))

    # Priority
    t_high = mgr.create("High task", priority="high")
    results.append(log_test("Priority", t_high.priority == TodoPriority.HIGH))

    # Blocking
    mgr.set_status(t_high.id, "blocked")
    results.append(log_test("Block", mgr.get(t_high.id).status == TodoStatus.BLOCKED))

    return all(results)


# ═══════════════════════════════════════════════════════
# Executor Tests (sync parts)
# ═══════════════════════════════════════════════════════

def test_executor_sync():
    section("Executor (Sync Parts)")
    results = []

    registry = ToolRegistry()
    meta = ToolMetadata(
        id="echo",
        name="Echo",
        description="Echo back input",
        category=ToolCategory.EXECUTION,
        input_schema={"type": "object", "properties": {"text": {"type": "string"}}},
        risk_level=RiskLevel.SAFE,
    )

    async def echo_executor(tool_id, args):
        return f"echo: {args.get('text', '')}"

    registry.register(meta, echo_executor)

    permissions = PermissionEngine()
    events = EventBus()

    async def auto_approve(meta, args, tool_name):
        return "allow_once"

    executor = ToolExecutor(registry, permissions, events, approval_callback=auto_approve)

    results.append(log_test("Create executor", executor is not None))
    results.append(log_test("History empty", len(executor.history) == 0))
    results.append(log_test("Active count = 0", executor.active_count == 0))

    # Execution record
    record = ToolExecution(tool_name="echo", arguments={"text": "hello"})
    results.append(log_test("ToolExecution dataclass", record.tool_name == "echo" and record.status == ExecutionStatus.PENDING))
    results.append(log_test("Execution to_dict", "tool_name" in record.to_dict()))

    # Unknown tool
    result = run_async(executor.execute("nonexistent", {}))
    results.append(log_test("Unknown tool error", "Error" in result or "Unknown" in result))

    # Simple execute
    result = run_async(executor.execute("echo", {"text": "hello world"}))
    results.append(log_test("Execute echo", result == "echo: hello world"))

    # History populated
    results.append(log_test("History has entries", len(executor.history) >= 2))

    # Recent
    recent = executor.recent(10)
    results.append(log_test("Recent entries", len(recent) >= 2))

    return all(results)


# ═══════════════════════════════════════════════════════
# Filesystem Tool Tests
# ═══════════════════════════════════════════════════════

def test_filesystem_tools():
    section("Filesystem Tools")
    results = []

    with tempfile.TemporaryDirectory() as tmpdir:
        # Write
        from leocode.tools.filesystem import register_filesystem_tools
        registry = ToolRegistry()
        register_filesystem_tools(registry, tmpdir)

        result = run_async(registry.execute("write", {"path": "test.txt", "content": "hello world"}))
        results.append(log_test("Write file", "Written" in result))

        # Read
        result = run_async(registry.execute("read", {"path": "test.txt"}))
        results.append(log_test("Read file", "hello world" in result))

        # Read with offset
        result = run_async(registry.execute("read", {"path": "test.txt", "offset": 0, "limit": 1}))
        results.append(log_test("Read with limit", "hello world" in result))

        # Read nonexistent
        result = run_async(registry.execute("read", {"path": "nope.txt"}))
        results.append(log_test("Read nonexistent", "not found" in result.lower() or "error" in result.lower()))

        # Edit
        result = run_async(registry.execute("edit", {
            "path": "test.txt",
            "old_string": "hello",
            "new_string": "goodbye",
        }))
        results.append(log_test("Edit file", "Edited" in result))

        content = Path(tmpdir, "test.txt").read_text()
        results.append(log_test("Edit verified", "goodbye world" in content))

        # Edit nonexistent string
        result = run_async(registry.execute("edit", {
            "path": "test.txt",
            "old_string": "hello",
            "new_string": "nope",
        }))
        results.append(log_test("Edit missing string", "not found" in result.lower() or "error" in result.lower()))

        # List dir
        result = run_async(registry.execute("list_dir", {"path": "."}))
        results.append(log_test("List dir", "test.txt" in result))

        # Glob
        result = run_async(registry.execute("glob", {"pattern": "*.txt"}))
        results.append(log_test("Glob", "test.txt" in result))

        # Glob no match
        result = run_async(registry.execute("glob", {"pattern": "*.xyz"}))
        results.append(log_test("Glob no match", "No files" in result or "no files" in result.lower()))

    return all(results)


# ═══════════════════════════════════════════════════════
# Execution Tool Tests
# ═══════════════════════════════════════════════════════

def test_shell_tool():
    section("Shell Tool")
    results = []

    from leocode.tools.execution import register_execution_tools
    registry = ToolRegistry()
    register_execution_tools(registry, tempfile.gettempdir())

    # Simple command
    result = run_async(registry.execute("shell", {"command": "echo hello"}))
    results.append(log_test("Shell echo", "hello" in result))

    # Command with exit code
    result = run_async(registry.execute("shell", {"command": "false"}))
    results.append(log_test("Shell exit code", "exit code" in result.lower()))

    # Empty command
    result = run_async(registry.execute("shell", {"command": ""}))
    results.append(log_test("Shell empty", "error" in result.lower() or "no command" in result.lower()))

    return all(results)


# ═══════════════════════════════════════════════════════
# Integration: Registry + Executor + Permissions
# ═══════════════════════════════════════════════════════

def test_integration():
    section("Integration: Registry + Executor + Permissions")
    results = []

    with tempfile.TemporaryDirectory() as tmpdir:
        registry = ToolRegistry()
        permissions = PermissionEngine()
        events = EventBus()
        from leocode.tools.filesystem import register_filesystem_tools
        from leocode.tools.execution import register_execution_tools
        register_filesystem_tools(registry, tmpdir)
        register_execution_tools(registry, tmpdir)

        event_log = []
        async def log_events(event: Event):
            event_log.append(event.type.value)

        events.subscribe(EventType.TOOL_PENDING, log_events)
        events.subscribe(EventType.TOOL_STARTED, log_events)
        events.subscribe(EventType.TOOL_COMPLETED, log_events)

        # Mock approval callback that always allows
        async def auto_approve(meta, args, tool_name):
            return "allow_once"

        executor = ToolExecutor(registry, permissions, events, approval_callback=auto_approve)

        # Execute safe tool (no approval needed)
        result = run_async(executor.execute("write", {"path": "test.py", "content": "print('hi')"}))
        results.append(log_test("Execute write via executor", "Written" in result))
        results.append(log_test("Events emitted", len(event_log) >= 3))

        # Read back
        result = run_async(executor.execute("read", {"path": "test.py"}))
        results.append(log_test("Read back written file", "print" in result))

        # Shell tool
        result = run_async(executor.execute("shell", {"command": "echo integration"}))
        results.append(log_test("Shell via executor", "integration" in result))

    return all(results)


# ═══════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════

def main():
    print(f"\n{Colors.BOLD}{'═' * 60}{Colors.ENDC}")
    print(f"{Colors.BOLD}  LEOCODE TOOL SYSTEM — COMPREHENSIVE TESTS{Colors.ENDC}")
    print(f"{Colors.BOLD}{'═' * 60}{Colors.ENDC}")

    tests = [
        test_tool_registry,
        test_permission_engine,
        test_event_bus,
        test_todo_manager,
        test_executor_sync,
        test_filesystem_tools,
        test_shell_tool,
        test_integration,
    ]

    all_passed = True
    for test_fn in tests:
        try:
            if not test_fn():
                all_passed = False
        except Exception as e:
            print(f"\n{Colors.FAIL}  ✗ {test_fn.__name__} CRASHED: {e}{Colors.ENDC}")
            import traceback
            traceback.print_exc()
            all_passed = False

    print(f"\n{Colors.BOLD}{'═' * 60}{Colors.ENDC}")
    if all_passed:
        print(f"{Colors.PASS}{Colors.BOLD}  ALL TESTS PASSED ✓{Colors.ENDC}")
    else:
        print(f"{Colors.FAIL}{Colors.BOLD}  SOME TESTS FAILED ✗{Colors.ENDC}")
    print(f"{Colors.BOLD}{'═' * 60}{Colors.ENDC}\n")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
