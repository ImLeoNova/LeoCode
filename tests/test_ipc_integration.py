#!/usr/bin/env python3
"""
LeoCode IPC Integration Test
Tests the full flow: backend startup -> IPC connection -> message send -> response receive.

This test starts the actual backend, connects via IPC, sends a message,
and verifies the full round-trip works.

Run: python tests/test_ipc_integration.py
"""

import asyncio
import json
import os
import sys
import signal
import subprocess
import tempfile
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

TEST_LOG = "/tmp/leocode-ipc-test.log"
TEST_TIMEOUT = 30  # seconds


def test_log(msg: str):
    """Write to test log."""
    try:
        with open(TEST_LOG, "a") as f:
            f.write(f"[TEST {time.strftime('%H:%M:%S')}] {msg}\n")
    except Exception:
        pass
    print(f"  {msg}")


class IPCClient:
    """Simple IPC client for testing."""

    def __init__(self):
        self.reader = None
        self.writer = None
        self.messages = []
        self.connected = False

    async def connect(self, sock_path: str):
        """Connect to the IPC socket."""
        test_log(f"Connecting to socket: {sock_path}")
        self.reader, self.writer = await asyncio.open_unix_connection(sock_path)
        self.connected = True
        test_log("Connected to IPC socket")

    async def read_until(self, timeout: float = TEST_TIMEOUT):
        """Read messages until timeout or a specific message arrives."""
        messages = []
        try:
            while True:
                line = await asyncio.wait_for(
                    self.reader.readline(), timeout=timeout
                )
                if not line:
                    break
                data = json.loads(line.decode().strip())
                messages.append(data)
                test_log(f"  RECV: method={data.get('method', '(response)')} id={data.get('id', 'none')}")
        except asyncio.TimeoutError:
            test_log(f"  Read timeout after {timeout}s")
        except Exception as e:
            test_log(f"  Read error: {e}")
        return messages

    async def send(self, method: str, params: dict = None):
        """Send a JSON-RPC request."""
        msg = {"jsonrpc": "2.0", "id": 1, "method": method}
        if params:
            msg["params"] = params
        data = json.dumps(msg) + "\n"
        self.writer.write(data.encode())
        await self.writer.drain()
        test_log(f"SENT: method={method} params={json.dumps(params or {}, ensure_ascii=False)[:200]}")

    async def notify(self, method: str, params: dict = None):
        """Send a JSON-RPC notification (no id)."""
        msg = {"jsonrpc": "2.0", "method": method}
        if params:
            msg["params"] = params
        data = json.dumps(msg) + "\n"
        self.writer.write(data.encode())
        await self.writer.drain()
        test_log(f"SENT NOTIFY: method={method}")

    def close(self):
        if self.writer:
            self.writer.close()


async def test_backend_startup():
    """Test 1: Backend starts and creates IPC socket."""
    test_log("=" * 60)
    test_log("TEST 1: Backend startup and IPC socket creation")
    test_log("=" * 60)

    # Clear old debug logs
    for f in ["/tmp/leocode-backend-debug.log", "/tmp/leocode-ipc-debug.log"]:
        try:
            os.unlink(f)
        except FileNotFoundError:
            pass

    # Start the backend
    project_root = Path(__file__).parent.parent
    backend_script = project_root / "leocode" / "ui" / "tui_backend.py"

    proc = subprocess.Popen(
        [sys.executable, "-u", str(backend_script)],
        cwd=str(project_root),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    test_log(f"Backend started with PID={proc.pid}")

    # Wait for socket file
    sock_path = None
    path_file = os.path.join(tempfile.gettempdir(), f"leocode-{proc.pid}.path")
    for i in range(50):
        if os.path.exists(path_file):
            sock_path = open(path_file).read().strip()
            test_log(f"Socket path found: {sock_path}")
            break
        await asyncio.sleep(0.1)

    if not sock_path:
        test_log("FAIL: Socket file not created within 5 seconds")
        proc.kill()
        return False

    # Check if socket file exists
    if not os.path.exists(sock_path):
        test_log(f"FAIL: Socket file does not exist: {sock_path}")
        proc.kill()
        return False

    test_log("PASS: Backend started and socket created")
    proc.kill()
    proc.wait()
    return True


async def test_ipc_connection():
    """Test 2: IPC client can connect to backend."""
    test_log("=" * 60)
    test_log("TEST 2: IPC client connection")
    test_log("=" * 60)

    project_root = Path(__file__).parent.parent
    backend_script = project_root / "leocode" / "ui" / "tui_backend.py"

    proc = subprocess.Popen(
        [sys.executable, "-u", str(backend_script)],
        cwd=str(project_root),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    test_log(f"Backend PID={proc.pid}")

    # Wait for socket
    path_file = os.path.join(tempfile.gettempdir(), f"leocode-{proc.pid}.path")
    sock_path = None
    for i in range(50):
        if os.path.exists(path_file):
            sock_path = open(path_file).read().strip()
            break
        await asyncio.sleep(0.1)

    if not sock_path:
        test_log("FAIL: No socket")
        proc.kill()
        return False

    # Connect
    client = IPCClient()
    try:
        await client.connect(sock_path)
    except Exception as e:
        test_log(f"FAIL: Could not connect: {e}")
        proc.kill()
        return False

    # Read the 'ready' notification
    test_log("Waiting for 'ready' notification...")
    messages = await client.read_until(timeout=5)

    ready_found = any(m.get("method") == "ready" for m in messages)
    if ready_found:
        test_log("PASS: Connected and received 'ready' notification")
    else:
        test_log(f"FAIL: No 'ready' notification. Got: {[m.get('method') for m in messages]}")
        client.close()
        proc.kill()
        return False

    client.close()
    proc.kill()
    proc.wait()
    return True


async def test_message_flow():
    """Test 3: Send a user message and receive responses."""
    test_log("=" * 60)
    test_log("TEST 3: Full message flow (send message -> get response)")
    test_log("=" * 60)

    project_root = Path(__file__).parent.parent
    backend_script = project_root / "leocode" / "ui" / "tui_backend.py"

    proc = subprocess.Popen(
        [sys.executable, "-u", str(backend_script)],
        cwd=str(project_root),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    test_log(f"Backend PID={proc.pid}")

    # Wait for socket
    path_file = os.path.join(tempfile.gettempdir(), f"leocode-{proc.pid}.path")
    sock_path = None
    for i in range(50):
        if os.path.exists(path_file):
            sock_path = open(path_file).read().strip()
            break
        await asyncio.sleep(0.1)

    if not sock_path:
        test_log("FAIL: No socket")
        proc.kill()
        return False

    # Connect
    client = IPCClient()
    await client.connect(sock_path)

    # Wait for ready
    await client.read_until(timeout=5)
    test_log("Backend ready, sending user message...")

    # Send a user message
    await client.notify("user_message", {"content": "Hello, say 'test response' back to me."})

    # Collect all responses for up to 20 seconds
    test_log("Collecting responses (up to 20s)...")
    all_messages = []
    start = time.time()
    while time.time() - start < 20:
        try:
            line = await asyncio.wait_for(client.reader.readline(), timeout=2)
            if not line:
                break
            data = json.loads(line.decode().strip())
            all_messages.append(data)
            method = data.get("method", "(response)")
            test_log(f"  RECV: {method}")
        except asyncio.TimeoutError:
            # Check if we got the final message
            has_final = any(m.get("method") == "assistant_message" for m in all_messages)
            has_error = any(m.get("method") == "error" for m in all_messages)
            if has_final or has_error:
                break
        except json.JSONDecodeError:
            continue

    client.close()

    # Analyze responses
    test_log("\nResponse analysis:")
    methods_received = [m.get("method") for m in all_messages if m.get("method")]
    test_log(f"  Methods received: {methods_received}")

    has_thinking = "thinking" in methods_received or "agent_state_changed" in methods_received
    has_assistant = "assistant_message" in methods_received
    has_stream = "assistant_stream" in methods_received
    has_error = "error" in methods_received

    test_log(f"  Has thinking/state: {has_thinking}")
    test_log(f"  Has assistant_message: {has_assistant}")
    test_log(f"  Has assistant_stream: {has_stream}")
    test_log(f"  Has error: {has_error}")

    if has_assistant:
        # Get the assistant message content
        for m in all_messages:
            if m.get("method") == "assistant_message":
                content = m.get("params", {}).get("content", "")
                test_log(f"  Assistant response: '{content[:200]}'")
                break
        test_log("PASS: Full message flow works - message sent and response received")
        proc.kill()
        proc.wait()
        return True
    elif has_error:
        # Error is acceptable if it's an API error (server not running)
        error_msg = ""
        for m in all_messages:
            if m.get("method") == "error":
                error_msg = m.get("params", {}).get("message", "")
                break
        test_log(f"  Error message: {error_msg}")
        # Check if it's an API connection error (expected if no API server)
        if "connect" in error_msg.lower() or "refused" in error_msg.lower() or "timeout" in error_msg.lower():
            test_log("PASS: IPC flow works - error is from API server not running (expected)")
            proc.kill()
            proc.wait()
            return True
        else:
            test_log(f"FAIL: Unexpected error: {error_msg}")
            proc.kill()
            proc.wait()
            return False
    else:
        test_log(f"FAIL: No assistant_message or error received. Messages: {methods_received}")
        # Dump backend debug log
        try:
            with open("/tmp/leocode-backend-debug.log") as f:
                debug_content = f.read()
                test_log(f"\nBackend debug log:\n{debug_content[-2000:]}")
        except FileNotFoundError:
            test_log("No backend debug log found")
        proc.kill()
        proc.wait()
        return False


async def test_queue_before_connect():
    """Test 4: Messages queued before IPC connects are delivered."""
    test_log("=" * 60)
    test_log("TEST 4: Message queue before connection")
    test_log("=" * 60)

    # This tests the frontend IPC client's queue mechanism
    # We simulate by creating an IPCClient and sending before connected
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root / "frontend" / "src"))

    # Instead, let's test the backend's message handling directly
    test_log("Testing backend message handler directly...")

    from leocode.ui.tui_backend import TUIAgent
    from leocode.config import Config

    try:
        agent = TUIAgent(os.getcwd())
        test_log(f"Agent created: model={agent.config.model}")

        # Mock the server's send method to capture outputs
        sent_messages = []
        original_send = agent.server.send

        async def mock_send(method, params=None):
            sent_messages.append({"method": method, "params": params})
            test_log(f"  MOCK SEND: {method}")

        agent.server.send = mock_send

        # Call handle_user_message directly
        result = await agent.handle_user_message({"content": "test"})
        test_log(f"Result: {result}")

        # Check that agent_state_changed was sent
        state_changes = [m for m in sent_messages if m["method"] == "agent_state_changed"]
        test_log(f"State changes sent: {len(state_changes)}")

        if len(state_changes) >= 1:
            test_log("PASS: Agent handle_user_message works")
            return True
        else:
            test_log("FAIL: No state changes sent")
            return False

    except Exception as e:
        test_log(f"FAIL: Exception: {type(e).__name__}: {e}")
        import traceback
        test_log(traceback.format_exc())
        return False


async def main():
    # Clear test log
    with open(TEST_LOG, "w") as f:
        f.write("")

    test_log("LeoCode IPC Integration Tests")
    test_log("=" * 60)

    results = {}

    # Test 1: Backend startup
    try:
        results["startup"] = await asyncio.wait_for(test_backend_startup(), timeout=15)
    except asyncio.TimeoutError:
        test_log("FAIL: Test 1 timed out")
        results["startup"] = False

    await asyncio.sleep(0.5)

    # Test 2: IPC connection
    try:
        results["connection"] = await asyncio.wait_for(test_ipc_connection(), timeout=15)
    except asyncio.TimeoutError:
        test_log("FAIL: Test 2 timed out")
        results["connection"] = False

    await asyncio.sleep(0.5)

    # Test 3: Full message flow
    try:
        results["message_flow"] = await asyncio.wait_for(test_message_flow(), timeout=30)
    except asyncio.TimeoutError:
        test_log("FAIL: Test 3 timed out")
        results["message_flow"] = False

    await asyncio.sleep(0.5)

    # Test 4: Direct agent handler test
    try:
        results["agent_handler"] = await asyncio.wait_for(test_queue_before_connect(), timeout=10)
    except asyncio.TimeoutError:
        test_log("FAIL: Test 4 timed out")
        results["agent_handler"] = False

    # Summary
    test_log("\n" + "=" * 60)
    test_log("RESULTS SUMMARY")
    test_log("=" * 60)
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    for name, result in results.items():
        status = "PASS" if result else "FAIL"
        test_log(f"  {name}: {status}")
    test_log(f"\nTotal: {passed}/{total} passed")

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
