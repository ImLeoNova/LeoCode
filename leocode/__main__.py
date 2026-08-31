"""LeoCode CLI entry point."""

import sys
import os
import argparse


def main():
    parser = argparse.ArgumentParser(
        prog="leocode",
        description="LeoCode - AI Coding Agent",
    )
    parser.add_argument("-d", "--dir", default="", help="Working directory")
    parser.add_argument("-m", "--model", default="", help="Model to use")
    parser.add_argument("-u", "--url", default="", help="API base URL")
    parser.add_argument("-k", "--api-key", default="", help="API key")
    parser.add_argument("--no-agent", action="store_true", help="Disable agent mode")
    parser.add_argument("--legacy", action="store_true", help="Use old Textual UI")
    parser.add_argument("--version", action="version", version="LeoCode 1.0.0")

    args = parser.parse_args()

    working_dir = args.dir or os.getcwd()

    if not os.path.isdir(working_dir):
        print(f"Error: Directory not found: {working_dir}", file=sys.stderr)
        sys.exit(1)

    os.chdir(working_dir)

    # Apply CLI overrides to config
    if args.url or args.api_key or args.model:
        from .config import Config
        config = Config.load()
        if args.url:
            config.base_url = args.url
        if args.api_key:
            config.api_key = args.api_key
        if args.model:
            config.model = args.model
        if args.no_agent:
            config.agent_mode = False
        config.save()

    if args.legacy:
        # Old Textual UI
        from .app import run_app
        run_app(working_dir=working_dir)
    else:
        # New Ink TUI (default)
        from .ui.launch_tui import launch
        launch()


if __name__ == "__main__":
    main()
