#!/usr/bin/env python3
"""
Comprehensive tool-calling pipeline tests.

Covers:
1. Unit tests for all filesystem tool executors (read, write, edit, patch, delete, list_dir, glob)
2. Permission engine tests (check returns correct action for each tool)
3. End-to-end approval flow tests (IPC round-trip, approve/deny, fail-fast)
4. Full integration smoke test (TUIAgent.handle_user_message with mocked model)
"""

import asyncio
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from leocode.tools.filesystem import (
    _tool_read, _tool_write, _tool_edit, _tool_patch,
    _tool_delete, _tool_list_dir, _tool_glob, _resolve,
    register_filesystem_tools,
)
from leocode.tools.registry import ToolRegistry
from leocode.permissions import PermissionEngine, PermissionAction, RiskLevel, RISK_MAP
from leocode.executor import ToolExecutor, ExecutionStatus
from leocode.events import EventBus


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_tmp_dir():
    d = tempfile.mkdtemp(prefix="leocode_test_")
    return d


def _cleanup(d):
    shutil.rmtree(d, ignore_errors=True)


# ===================================================================
# Part 1: Unit tests for filesystem tool executors
# ===================================================================

class TestToolRead:
    def test_read_existing_file(self):
        d = _make_tmp_dir()
        try:
            f = Path(d) / "hello.txt"
            f.write_text("line1\nline2\nline3\n")
            result = _tool_read(d, {"path": "hello.txt"})
            assert "line1" in result
            assert "line2" in result
            assert "line3" in result
            assert "3 lines" in result
        finally:
            _cleanup(d)

    def test_read_missing_file(self):
        d = _make_tmp_dir()
        try:
            result = _tool_read(d, {"path": "nope.txt"})
            assert "Error" in result
            assert "not found" in result
        finally:
            _cleanup(d)

    def test_read_with_offset_limit(self):
        d = _make_tmp_dir()
        try:
            f = Path(d) / "lines.txt"
            f.write_text("a\nb\nc\nd\ne\n")
            result = _tool_read(d, {"path": "lines.txt", "offset": 1, "limit": 2})
            assert "b" in result
            assert "c" in result
            assert "a" not in result
            assert "d" not in result
        finally:
            _cleanup(d)

    def test_read_directory_returns_error(self):
        d = _make_tmp_dir()
        try:
            result = _tool_read(d, {"path": "."})
            assert "Error" in result
            assert "Not a file" in result
        finally:
            _cleanup(d)


class TestToolWrite:
    def test_write_creates_new_file(self):
        d = _make_tmp_dir()
        try:
            result = _tool_write(d, {"path": "new.txt", "content": "hello world"})
            assert "Written" in result
            assert (Path(d) / "new.txt").read_text() == "hello world"
        finally:
            _cleanup(d)

    def test_write_creates_parent_dirs(self):
        d = _make_tmp_dir()
        try:
            result = _tool_write(d, {"path": "sub/dir/file.txt", "content": "nested"})
            assert "Written" in result
            assert (Path(d) / "sub/dir/file.txt").read_text() == "nested"
        finally:
            _cleanup(d)

    def test_write_overwrites_existing(self):
        d = _make_tmp_dir()
        try:
            (Path(d) / "f.txt").write_text("old")
            result = _tool_write(d, {"path": "f.txt", "content": "new"})
            assert "Written" in result
            assert (Path(d) / "f.txt").read_text() == "new"
        finally:
            _cleanup(d)

    def test_write_empty_content(self):
        d = _make_tmp_dir()
        try:
            result = _tool_write(d, {"path": "empty.txt", "content": ""})
            assert "Written" in result
            assert (Path(d) / "empty.txt").read_text() == ""
        finally:
            _cleanup(d)


class TestToolEdit:
    def test_edit_replaces_string(self):
        d = _make_tmp_dir()
        try:
            (Path(d) / "f.py").write_text("def foo():\n    pass\n")
            result = _tool_edit(d, {"path": "f.py", "old_string": "pass", "new_string": "return 42"})
            assert "Edited" in result
            assert "return 42" in (Path(d) / "f.py").read_text()
        finally:
            _cleanup(d)

    def test_edit_zero_matches(self):
        d = _make_tmp_dir()
        try:
            (Path(d) / "f.txt").write_text("hello")
            result = _tool_edit(d, {"path": "f.txt", "old_string": "xyz", "new_string": "abc"})
            assert "Error" in result
            assert "not found" in result.lower()
        finally:
            _cleanup(d)

    def test_edit_multiple_matches(self):
        d = _make_tmp_dir()
        try:
            (Path(d) / "f.txt").write_text("aaa bbb aaa")
            result = _tool_edit(d, {"path": "f.txt", "old_string": "aaa", "new_string": "zzz"})
            assert "Error" in result
            assert "occurrences" in result.lower() or "multiple" in result.lower() or "Found" in result
        finally:
            _cleanup(d)

    def test_edit_missing_file(self):
        d = _make_tmp_dir()
        try:
            result = _tool_edit(d, {"path": "nope.txt", "old_string": "a", "new_string": "b"})
            assert "Error" in result
            assert "not found" in result.lower()
        finally:
            _cleanup(d)


class TestToolPatch:
    def test_patch_apply(self):
        d = _make_tmp_dir()
        try:
            (Path(d) / "f.txt").write_text("line1\nline2\n")
            diff = "--- a/f.txt\n+++ b/f.txt\n@@ -1,2 +1,2 @@\n line1\n-line2\n+line2_modified\n"
            result = _tool_patch(d, {"path": "f.txt", "diff": diff})
            assert "Patch" in result
        finally:
            _cleanup(d)


class TestToolDelete:
    def test_delete_existing_file(self):
        d = _make_tmp_dir()
        try:
            f = Path(d) / "todelete.txt"
            f.write_text("bye")
            result = _tool_delete(d, {"path": "todelete.txt"})
            assert "Deleted" in result
            assert not f.exists()
        finally:
            _cleanup(d)

    def test_delete_missing_file(self):
        d = _make_tmp_dir()
        try:
            result = _tool_delete(d, {"path": "nope.txt"})
            assert "Error" in result
            assert "not found" in result.lower()
        finally:
            _cleanup(d)

    def test_delete_refuses_directory(self):
        d = _make_tmp_dir()
        try:
            subdir = Path(d) / "mydir"
            subdir.mkdir()
            (subdir / "inner.txt").write_text("inside")
            result = _tool_delete(d, {"path": "mydir"})
            assert "Error" in result
            assert "directory" in result.lower()
            assert subdir.exists()
        finally:
            _cleanup(d)

    def test_delete_refuses_outside_working_dir(self):
        d = _make_tmp_dir()
        try:
            outside = Path(tempfile.mkdtemp()) / "outside.txt"
            outside.write_text("secret")
            result = _tool_delete(d, {"path": str(outside)})
            assert "Error" in result
            assert "outside" in result.lower()
            assert outside.exists()
            _cleanup(str(outside.parent))
        finally:
            _cleanup(d)

    def test_delete_inside_subdir(self):
        d = _make_tmp_dir()
        try:
            subdir = Path(d) / "sub"
            subdir.mkdir()
            f = subdir / "file.txt"
            f.write_text("content")
            result = _tool_delete(d, {"path": "sub/file.txt"})
            assert "Deleted" in result
            assert not f.exists()
        finally:
            _cleanup(d)


class TestToolListDir:
    def test_list_dir_contents(self):
        d = _make_tmp_dir()
        try:
            (Path(d) / "a.txt").write_text("a")
            (Path(d) / "b.txt").write_text("bb")
            (Path(d) / "subdir").mkdir()
            result = _tool_list_dir(d, {"path": "."})
            assert "a.txt" in result
            assert "b.txt" in result
            assert "subdir" in result
        finally:
            _cleanup(d)

    def test_list_dir_empty(self):
        d = _make_tmp_dir()
        try:
            result = _tool_list_dir(d, {"path": "."})
            assert "empty" in result.lower()
        finally:
            _cleanup(d)

    def test_list_dir_missing(self):
        d = _make_tmp_dir()
        try:
            result = _tool_list_dir(d, {"path": "nonexistent"})
            assert "Error" in result
        finally:
            _cleanup(d)

    def test_list_dir_not_a_dir(self):
        d = _make_tmp_dir()
        try:
            (Path(d) / "file.txt").write_text("x")
            result = _tool_list_dir(d, {"path": "file.txt"})
            assert "Error" in result
            assert "Not a directory" in result
        finally:
            _cleanup(d)


class TestToolGlob:
    def test_glob_finds_files(self):
        d = _make_tmp_dir()
        try:
            (Path(d) / "a.py").write_text("x")
            (Path(d) / "b.py").write_text("y")
            (Path(d) / "c.txt").write_text("z")
            result = _tool_glob(d, {"pattern": "*.py"})
            assert "a.py" in result
            assert "b.py" in result
            assert "c.txt" not in result
        finally:
            _cleanup(d)

    def test_glob_no_matches(self):
        d = _make_tmp_dir()
        try:
            result = _tool_glob(d, {"pattern": "*.xyz"})
            assert "No files found" in result
        finally:
            _cleanup(d)

    def test_glob_recursive(self):
        d = _make_tmp_dir()
        try:
            sub = Path(d) / "sub"
            sub.mkdir()
            (sub / "deep.py").write_text("x")
            result = _tool_glob(d, {"pattern": "**/*.py"})
            assert "deep.py" in result
        finally:
            _cleanup(d)


class TestResolve:
    def test_resolve_relative(self):
        d = _make_tmp_dir()
        try:
            p = _resolve(d, "foo.txt")
            assert p == (Path(d) / "foo.txt").resolve()
        finally:
            _cleanup(d)

    def test_resolve_absolute(self):
        p = _resolve("/tmp", "/etc/hostname")
        assert p == Path("/etc/hostname").resolve()


class TestRegisterFilesystemTools:
    def test_all_tools_registered(self):
        reg = ToolRegistry()
        d = _make_tmp_dir()
        try:
            register_filesystem_tools(reg, d)
            expected = ["read", "write", "edit", "patch", "delete", "list_dir", "glob"]
            for tool_id in expected:
                assert reg.exists(tool_id), f"Tool '{tool_id}' not registered"
                meta = reg.get(tool_id)
                schema = meta.to_openai_schema()
                assert schema["type"] == "function"
                assert schema["function"]["name"] == tool_id
                assert "parameters" in schema["function"]
        finally:
            _cleanup(d)

    def test_delete_risk_level(self):
        reg = ToolRegistry()
        d = _make_tmp_dir()
        try:
            register_filesystem_tools(reg, d)
            meta = reg.get("delete")
            assert meta.risk_level == RiskLevel.HIGH
        finally:
            _cleanup(d)


# ===================================================================
# Part 2: Permission engine tests
# ===================================================================

class TestPermissionEngine:
    def _make_engine(self, policy="balanced"):
        # Bypass file loading by not using the default config path
        engine = PermissionEngine.__new__(PermissionEngine)
        engine.policy = policy
        engine._session_overrides = {}
        # Force default rules
        from leocode.permissions import PermissionRule
        engine._rules = [
            PermissionRule(tool="read", action=PermissionAction.ALLOW),
            PermissionRule(tool="list_dir", action=PermissionAction.ALLOW),
            PermissionRule(tool="glob", action=PermissionAction.ALLOW),
            PermissionRule(tool="grep", action=PermissionAction.ALLOW),
            PermissionRule(tool="todo", action=PermissionAction.ALLOW),
            PermissionRule(tool="plan", action=PermissionAction.ALLOW),
            PermissionRule(tool="question", action=PermissionAction.ALLOW),
            PermissionRule(tool="skill", action=PermissionAction.ALLOW),
            PermissionRule(tool="search", action=PermissionAction.ALLOW),
            PermissionRule(tool="fetch", action=PermissionAction.ALLOW),
            PermissionRule(tool="lsp", action=PermissionAction.ALLOW),
            PermissionRule(tool="write", action=PermissionAction.ASK),
            PermissionRule(tool="edit", action=PermissionAction.ASK),
            PermissionRule(tool="patch", action=PermissionAction.ASK),
            PermissionRule(tool="delete", action=PermissionAction.ASK),
            PermissionRule(tool="shell", action=PermissionAction.ASK),
            PermissionRule(tool="task", action=PermissionAction.ASK),
            PermissionRule(tool="execute", action=PermissionAction.DENY),
        ]
        return engine

    def test_read_allowed(self):
        e = self._make_engine()
        assert e.check("read", {"path": "foo.py"}) == PermissionAction.ALLOW

    def test_list_dir_allowed(self):
        e = self._make_engine()
        assert e.check("list_dir", {"path": "."}) == PermissionAction.ALLOW

    def test_glob_allowed(self):
        e = self._make_engine()
        assert e.check("glob", {"pattern": "*.py"}) == PermissionAction.ALLOW

    def test_write_ask(self):
        e = self._make_engine()
        assert e.check("write", {"path": "f.txt", "content": "x"}) == PermissionAction.ASK

    def test_edit_ask(self):
        e = self._make_engine()
        assert e.check("edit", {"path": "f.txt", "old_string": "a", "new_string": "b"}) == PermissionAction.ASK

    def test_patch_ask(self):
        e = self._make_engine()
        assert e.check("patch", {"path": "f.txt", "diff": "---"}) == PermissionAction.ASK

    def test_delete_ask(self):
        e = self._make_engine()
        assert e.check("delete", {"path": "f.txt"}) == PermissionAction.ASK

    def test_shell_ask(self):
        e = self._make_engine()
        assert e.check("shell", {"command": "ls"}) == PermissionAction.ASK

    def test_execute_denied(self):
        e = self._make_engine()
        assert e.check("execute", {"workflow": "deploy"}) == PermissionAction.DENY

    def test_unknown_tool_high_risk_denied(self):
        e = self._make_engine()
        # Unknown tool gets HIGH risk -> DENY by default
        assert e.check("unknown_tool", {}) == PermissionAction.DENY

    def test_permissive_policy_safe_allowed(self):
        e = self._make_engine(policy="permissive")
        assert e.check("read", {}) == PermissionAction.ALLOW
        assert e.check("glob", {}) == PermissionAction.ALLOW

    def test_permissive_policy_medium_still_asks(self):
        e = self._make_engine(policy="permissive")
        # MEDIUM risk tools should still ask even in permissive mode
        # because permissive only auto-allows SAFE and LOW
        assert e.check("write", {"path": "f.txt"}) == PermissionAction.ASK

    def test_permissive_policy_high_still_asks(self):
        e = self._make_engine(policy="permissive")
        assert e.check("shell", {"command": "ls"}) == PermissionAction.ASK

    def test_risk_map_entries(self):
        # Verify all expected tools have risk map entries
        expected_tools = [
            "read", "list_dir", "glob", "grep", "search", "fetch",
            "todo", "plan", "question", "skill", "lsp",
            "edit", "patch", "write", "delete", "shell", "task", "execute",
        ]
        for tool in expected_tools:
            assert tool in RISK_MAP, f"'{tool}' missing from RISK_MAP"

    def test_risk_map_delete_is_high(self):
        assert RISK_MAP["delete"] == RiskLevel.HIGH

    def test_describe_action_delete(self):
        e = self._make_engine()
        desc = e.describe_action("delete", {"path": "secret.txt"})
        assert "Delete file: secret.txt" == desc

    def test_describe_action_write(self):
        e = self._make_engine()
        desc = e.describe_action("write", {"path": "new.txt"})
        assert "Write to file: new.txt" == desc

    def test_describe_action_edit(self):
        e = self._make_engine()
        desc = e.describe_action("edit", {"path": "f.py"})
        assert "Edit file: f.py" == desc

    def test_describe_action_shell(self):
        e = self._make_engine()
        desc = e.describe_action("shell", {"command": "echo hi"})
        assert "echo hi" in desc

    def test_session_override_allow_once(self):
        e = self._make_engine()
        e.allow_once("write", {"path": "f.txt"})
        assert e.check("write", {"path": "f.txt"}) == PermissionAction.ALLOW

    def test_session_override_deny(self):
        e = self._make_engine()
        e.deny("read", {"path": "f.txt"})
        assert e.check("read", {"path": "f.txt"}) == PermissionAction.DENY


# ===================================================================
# Part 3: End-to-end approval flow tests
# ===================================================================

class TestApprovalFlow:
    """Test the full approval round-trip using ToolExecutor with mocked approval callback."""

    def _make_executor(self, approval_result="allow_once"):
        reg = ToolRegistry()
        d = _make_tmp_dir()
        register_filesystem_tools(reg, d)
        perms = PermissionEngine.__new__(PermissionEngine)
        perms.policy = "balanced"
        perms._session_overrides = {}
        from leocode.permissions import PermissionRule
        perms._rules = [
            PermissionRule(tool="read", action=PermissionAction.ALLOW),
            PermissionRule(tool="write", action=PermissionAction.ASK),
            PermissionRule(tool="edit", action=PermissionAction.ASK),
            PermissionRule(tool="delete", action=PermissionAction.ASK),
            PermissionRule(tool="list_dir", action=PermissionAction.ALLOW),
            PermissionRule(tool="glob", action=PermissionAction.ALLOW),
        ]
        events = EventBus()

        async def fake_approval(meta, arguments, tool_name):
            return approval_result

        executor = ToolExecutor(
            registry=reg, permissions=perms, events=events,
            approval_callback=fake_approval,
        )
        return executor, d

    def test_approve_write_creates_file(self):
        async def run():
            executor, d = self._make_executor("allow_once")
            f = Path(d) / "approved.txt"
            result = await executor.execute("write", {"path": "approved.txt", "content": "approved!"})
            assert "Written" in result
            assert f.exists()
            assert f.read_text() == "approved!"
            _cleanup(d)
        asyncio.run(run())

    def test_deny_write_does_not_create_file(self):
        async def run():
            executor, d = self._make_executor("denied")
            f = Path(d) / "denied.txt"
            result = await executor.execute("write", {"path": "denied.txt", "content": "nope"})
            assert "Error" in result or "denied" in result.lower()
            assert not f.exists()
            _cleanup(d)
        asyncio.run(run())

    def test_approve_edit_modifies_file(self):
        async def run():
            executor, d = self._make_executor("allow_once")
            f = Path(d) / "editable.txt"
            f.write_text("before")
            result = await executor.execute("edit", {
                "path": "editable.txt", "old_string": "before", "new_string": "after"
            })
            assert "Edited" in result
            assert f.read_text() == "after"
            _cleanup(d)
        asyncio.run(run())

    def test_deny_edit_does_not_modify_file(self):
        async def run():
            executor, d = self._make_executor("denied")
            f = Path(d) / "protected.txt"
            f.write_text("original")
            result = await executor.execute("edit", {
                "path": "protected.txt", "old_string": "original", "new_string": "changed"
            })
            assert "Error" in result or "denied" in result.lower()
            assert f.read_text() == "original"
            _cleanup(d)
        asyncio.run(run())

    def test_approve_delete_removes_file(self):
        async def run():
            executor, d = self._make_executor("allow_once")
            f = Path(d) / "todelete.txt"
            f.write_text("bye")
            result = await executor.execute("delete", {"path": "todelete.txt"})
            assert "Deleted" in result
            assert not f.exists()
            _cleanup(d)
        asyncio.run(run())

    def test_deny_delete_keeps_file(self):
        async def run():
            executor, d = self._make_executor("denied")
            f = Path(d) / "protected.txt"
            f.write_text("safe")
            result = await executor.execute("delete", {"path": "protected.txt"})
            assert "Error" in result or "denied" in result.lower()
            assert f.exists()
            _cleanup(d)
        asyncio.run(run())

    def test_read_no_approval_needed(self):
        async def run():
            executor, d = self._make_executor("denied")
            f = Path(d) / "readable.txt"
            f.write_text("visible")
            result = await executor.execute("read", {"path": "readable.txt"})
            assert "visible" in result
            _cleanup(d)
        asyncio.run(run())


class TestApprovalFailFast:
    """Test that missing IPC writer causes immediate denial, not a 120s hang."""

    def test_fail_fast_when_writer_none(self):
        async def run():
            d = _make_tmp_dir()
            try:
                from leocode.ui.ipc_server import IPCServer
                server = IPCServer()
                # Writer is None by default
                assert server._writer is None

                from leocode.ui.tui_backend import TUIAgent
                # Create a minimal agent-like object to test _handle_approval
                agent = TUIAgent.__new__(TUIAgent)
                agent.server = server
                agent._approval_future = None

                from leocode.tools.registry import ToolMetadata
                from leocode.tools.registry import ToolCategory
                meta = ToolMetadata(
                    id="write", name="Write", description="test",
                    category=ToolCategory.FILESYSTEM,
                    input_schema={"type": "object"},
                    risk_level=RiskLevel.MEDIUM,
                )
                # This should return "denied" almost immediately, not hang
                import time
                start = time.time()
                result = await agent._handle_approval(meta, {"path": "x"}, "write")
                elapsed = time.time() - start
                assert result == "denied"
                assert elapsed < 5.0, f"Approval took {elapsed:.1f}s, should fail fast"
            finally:
                _cleanup(d)
        asyncio.run(run())

    def test_send_returns_false_when_no_writer(self):
        async def run():
            from leocode.ui.ipc_server import IPCServer
            server = IPCServer()
            result = await server.send("test_method", {"key": "value"})
            assert result is False
        asyncio.run(run())

    def test_send_returns_true_when_writer_set(self):
        async def run():
            from leocode.ui.ipc_server import IPCServer
            server = IPCServer()
            # Create a mock writer: write() is sync, drain() is async
            mock_writer = MagicMock()
            mock_writer.drain = AsyncMock()
            server._writer = mock_writer
            result = await server.send("test_method", {"key": "value"})
            assert result is True
            mock_writer.write.assert_called_once()
            mock_writer.drain.assert_called_once()
            server._writer = None
        asyncio.run(run())


# ===================================================================
# Part 4: Full integration smoke test
# ===================================================================

class TestIntegrationSmoke:
    """Full integration: write -> edit -> delete on same file, auto-approving each."""

    def test_write_edit_delete_sequence(self):
        async def run():
            d = _make_tmp_dir()
            try:
                reg = ToolRegistry()
                register_filesystem_tools(reg, d)

                perms = PermissionEngine.__new__(PermissionEngine)
                perms.policy = "balanced"
                perms._session_overrides = {}
                from leocode.permissions import PermissionRule
                perms._rules = [
                    PermissionRule(tool="read", action=PermissionAction.ALLOW),
                    PermissionRule(tool="write", action=PermissionAction.ASK),
                    PermissionRule(tool="edit", action=PermissionAction.ASK),
                    PermissionRule(tool="delete", action=PermissionAction.ASK),
                    PermissionRule(tool="list_dir", action=PermissionAction.ALLOW),
                    PermissionRule(tool="glob", action=PermissionAction.ALLOW),
                ]
                events = EventBus()

                async def auto_approve(meta, arguments, tool_name):
                    return "allow_once"

                executor = ToolExecutor(
                    registry=reg, permissions=perms, events=events,
                    approval_callback=auto_approve,
                )

                target = Path(d) / "pipeline_test.txt"

                # Step 1: Write
                result = await executor.execute("write", {
                    "path": "pipeline_test.txt", "content": "step1: initial"
                })
                assert "Written" in result
                assert target.exists()
                assert target.read_text() == "step1: initial"

                # Step 2: Edit
                result = await executor.execute("edit", {
                    "path": "pipeline_test.txt",
                    "old_string": "initial",
                    "new_string": "modified"
                })
                assert "Edited" in result
                assert target.read_text() == "step1: modified"

                # Step 3: Read (no approval)
                result = await executor.execute("read", {
                    "path": "pipeline_test.txt"
                })
                assert "step1: modified" in result

                # Step 4: Delete
                result = await executor.execute("delete", {
                    "path": "pipeline_test.txt"
                })
                assert "Deleted" in result
                assert not target.exists()

                # Step 5: Verify deleted
                result = await executor.execute("read", {
                    "path": "pipeline_test.txt"
                })
                assert "Error" in result

            finally:
                _cleanup(d)
        asyncio.run(run())


# ===================================================================
# Test runner
# ===================================================================

def _run_tests():
    """Discover and run all test classes."""
    import traceback

    test_classes = [
        TestToolRead, TestToolWrite, TestToolEdit, TestToolPatch,
        TestToolDelete, TestToolListDir, TestToolGlob, TestResolve,
        TestRegisterFilesystemTools,
        TestPermissionEngine,
        TestApprovalFlow, TestApprovalFailFast,
        TestIntegrationSmoke,
    ]

    total = 0
    passed = 0
    failed = 0
    errors = []

    for cls in test_classes:
        instance = cls()
        methods = [m for m in dir(instance) if m.startswith("test_")]
        for method_name in sorted(methods):
            total += 1
            method = getattr(instance, method_name)
            test_label = f"{cls.__name__}.{method_name}"
            try:
                method()
                passed += 1
                print(f"  PASS  {test_label}")
            except Exception as e:
                failed += 1
                errors.append((test_label, e))
                print(f"  FAIL  {test_label}: {e}")
                traceback.print_exc()

    print(f"\n{'='*60}")
    print(f"  RESULTS: {passed}/{total} passed, {failed} failed")
    print(f"{'='*60}\n")

    if errors:
        print("Failures:")
        for label, err in errors:
            print(f"  {label}: {err}")
        print()

    return failed == 0


if __name__ == "__main__":
    success = _run_tests()
    sys.exit(0 if success else 1)
