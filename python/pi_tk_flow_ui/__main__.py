"""Standalone entry point for the tf-ui terminal app."""

from __future__ import annotations

import sys


def main(argv: list[str] | None = None) -> int:
    """Launch the standalone Ticketflow TUI or print web serve instructions."""
    import argparse
    
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

    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

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


if __name__ == "__main__":
    sys.exit(main())
