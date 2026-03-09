#!/usr/bin/env python3
"""Ralph Wiggum Loop - External ticket processor.

This module provides a CLI wrapper that invokes the tf-ralph-loop.sh shell script
from the same package directory.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    """Run the tf-ralph-loop.sh script with the same arguments."""
    # Find the script relative to this file (in the package directory)
    package_dir = Path(__file__).parent
    script_path = package_dir / "tf-ralph-loop.sh"

    if not script_path.exists():
        print(f"Error: tf-ralph-loop.sh not found at {script_path}", file=sys.stderr)
        return 1

    # Pass all arguments to the shell script
    return subprocess.call([str(script_path)] + sys.argv[1:])


if __name__ == "__main__":
    sys.exit(main())
