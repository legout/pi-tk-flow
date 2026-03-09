"""Unified tf CLI for pi-tk-flow."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    """Main entry point for the tf CLI."""
    import argparse

    parser = argparse.ArgumentParser(
        prog="tf",
        description="pi-tk-flow CLI - Unified command for ticket workflow management"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # tf ui
    ui_parser = subparsers.add_parser(
        "ui",
        help="Launch the Ticketflow TUI",
    )
    ui_parser.add_argument(
        "--web",
        action="store_true",
        help="Print the textual serve command for running the UI in a browser"
    )
    ui_parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind web server to (default: 127.0.0.1)"
    )
    ui_parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port for web server (default: 8000)"
    )
    ui_parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )

    # tf ralph / tf ralph-loop
    ralph_parser = subparsers.add_parser(
        "ralph",
        aliases=["ralph-loop"],
        help="Run the Ralph Wiggum Loop for automated ticket processing"
    )
    ralph_parser.add_argument(
        "--clarify",
        action="store_true",
        help="Run with clarify TUI (default)"
    )
    ralph_parser.add_argument(
        "--hands-free",
        action="store_true",
        help="Run in hands-free mode"
    )
    ralph_parser.add_argument(
        "--dispatch",
        action="store_true",
        help="Run in dispatch mode"
    )
    ralph_parser.add_argument(
        "--interactive",
        action="store_true",
        help="Run in interactive mode"
    )
    ralph_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without executing"
    )
    ralph_parser.add_argument(
        "--once",
        action="store_true",
        help="Process current queue once and exit"
    )
    ralph_parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    ralph_parser.add_argument(
        "--version",
        action="store_true",
        help="Show version information"
    )

    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    # No subcommand - show help
    if args.command is None:
        parser.print_help()
        return 0

    # tf ui
    if args.command == "ui":
        # Build argv for run_ui
        ui_argv = []
        if getattr(args, "web", False):
            ui_argv.append("--web")
        if getattr(args, "host", "127.0.0.1") != "127.0.0.1":
            ui_argv.extend(["--host", getattr(args, "host")])
        if getattr(args, "port", 8000) != 8000:
            ui_argv.extend(["--port", str(getattr(args, "port"))])
        if getattr(args, "debug", False):
            ui_argv.append("--debug")
        return run_ui(ui_argv)

    # tf ralph / tf ralph-loop
    if args.command in ("ralph", "ralph-loop"):
        return run_ralph(args)


def run_ui(ui_args: list[str] | None = None) -> int:
    """Run the TUI (standalone entry point for tf-ui CLI)."""
    import argparse
    
    if ui_args is None:
        ui_args = sys.argv[1:]
    
    parser = argparse.ArgumentParser(
        prog="pi-tk-flow-ui",
        description="Launch the Ticketflow UI (terminal or web)"
    )
    parser.add_argument(
        "--web",
        action="store_true",
        help="Print the textual serve command for running the UI in a browser"
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind web server to (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port for web server (default: 8000)"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )

    args = parser.parse_args(ui_args)

    # If --web flag is set, print the textual serve command
    if args.web:
        print("\n🌐 To serve the Ticketflow UI in a web browser, run:")
        print("")
        print(f'   textual serve "tf-ui" --host {args.host} --port {args.port}')
        print("")
        print("⚠️  WARNING: Security considerations for web serving:")
        print("   • The default host (127.0.0.1) only allows local access")
        print("   • Use --host 0.0.0.0 to bind to all interfaces (allows external access)")
        print("   • Binding to 0.0.0.0 exposes the UI on your network - ensure proper firewall rules")
        print("   • No authentication is provided - anyone with access can view tickets")
        print("")
        return 0
    
    # Check dependencies before importing app
    missing_deps = []
    
    try:
        import textual
    except ImportError:
        missing_deps.append("textual>=0.47.0")
    
    try:
        import yaml
    except ImportError:
        missing_deps.append("pyyaml>=6.0")
    
    if missing_deps:
        print("Error: UI dependencies not installed.", file=sys.stderr)
        print("", file=sys.stderr)
        print("Missing packages:", file=sys.stderr)
        for dep in missing_deps:
            print(f"  - {dep}", file=sys.stderr)
        print("", file=sys.stderr)
        print("Install with one of:", file=sys.stderr)
        print("  uv tool install --from '.[ui]' pi-tk-flow-ui --reinstall", file=sys.stderr)
        print("  uvx --from '.[ui]' pi-tk-flow-ui", file=sys.stderr)
        print("  # or for editable local development", file=sys.stderr)
        print("  pip install -e '.[ui]'", file=sys.stderr)
        return 1
    
    # Import and run the app
    try:
        from pi_tk_flow_ui.app import TicketflowApp
        
        app = TicketflowApp()
        app.run()
        return 0
    except Exception as e:
        print(f"Error starting TUI: {e}", file=sys.stderr)
        if args.debug:
            import traceback
            traceback.print_exc()
        return 1


def run_ralph(args) -> int:
    """Run the Ralph loop."""
    from pi_tk_flow_ui.tf_ralph_loop import main as ralph_main

    # Build argv for ralph loop
    argv = []

    if getattr(args, "clarify", False):
        argv.append("--clarify")
    if getattr(args, "hands_free", False):
        argv.append("--hands-free")
    if getattr(args, "dispatch", False):
        argv.append("--dispatch")
    if getattr(args, "interactive", False):
        argv.append("--interactive")
    if getattr(args, "dry_run", False):
        argv.append("--dry-run")
    if getattr(args, "once", False):
        argv.append("--once")
    if getattr(args, "verbose", False):
        argv.append("--verbose")
    if getattr(args, "version", False):
        argv.append("--version")

    return ralph_main(argv)


if __name__ == "__main__":
    sys.exit(main())
