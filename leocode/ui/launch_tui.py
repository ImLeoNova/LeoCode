"""
LeoCode TUI Launcher
Launches the Python backend (socket server) and TypeScript frontend (socket client).
Both processes run independently; the frontend has direct terminal access.
"""

import subprocess
import sys
import os
import signal
import tempfile
from pathlib import Path


def launch():
    """Launch the TUI with backend and frontend."""
    frontend_dir = Path(__file__).parent.parent.parent / "frontend"
    frontend_js = frontend_dir / "dist" / "index.js"
    backend_script = Path(__file__).parent / "tui_backend.py"

    # Build frontend if needed
    if not frontend_js.exists() or not (frontend_dir / "node_modules").exists():
        print("Building frontend...", file=sys.stderr)
        subprocess.run(["npm", "install"], cwd=frontend_dir, check=True,
                       capture_output=True)
        subprocess.run(["npm", "run", "build"], cwd=frontend_dir, check=True,
                       capture_output=True)

    if not frontend_js.exists():
        print(f"Error: Frontend not built at {frontend_js}", file=sys.stderr)
        print("Run: cd frontend && npm install && npm run build", file=sys.stderr)
        sys.exit(1)

    # Start the Python backend (socket server, no terminal stdin)
    backend_proc = subprocess.Popen(
        [sys.executable, "-u", str(backend_script)],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=sys.stderr,
    )

    # Pass backend PID so frontend can find the socket
    env = os.environ.copy()
    env["LEOCODE_BACKEND_PID"] = str(backend_proc.pid)

    # Give backend a moment to create the socket
    import time
    time.sleep(0.3)

    # Start the TypeScript frontend (has real terminal access)
    frontend_proc = subprocess.Popen(
        ["node", str(frontend_js)],
        env=env,
        stderr=sys.stderr,
    )

    # Handle signals
    def cleanup(signum=None, frame=None):
        for proc in [frontend_proc, backend_proc]:
            try:
                proc.terminate()
            except Exception:
                pass
        for proc in [frontend_proc, backend_proc]:
            try:
                proc.wait(timeout=2)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass
        # Clean up socket files
        for suffix in ['.sock', '.path']:
            try:
                os.unlink(os.path.join(tempfile.gettempdir(), f"leocode-{backend_proc.pid}{suffix}"))
            except FileNotFoundError:
                pass
        sys.exit(0)

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    try:
        frontend_proc.wait()
    except KeyboardInterrupt:
        cleanup()
    finally:
        cleanup()


if __name__ == "__main__":
    launch()
