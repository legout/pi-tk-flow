"""Regression tests for the tf-ralph-loop shell script."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "python" / "pi_tk_flow_ui" / "tf-ralph-loop.sh"


def _write_executable(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
    path.chmod(0o755)


def _make_mock_bin(tmp_path: Path, ready_lines: str) -> tuple[Path, Path, Path]:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()

    ready_file = tmp_path / "ready.txt"
    ready_file.write_text(ready_lines, encoding="utf-8")

    pi_log = tmp_path / "pi.log"

    _write_executable(
        bin_dir / "tk",
        f"""#!/usr/bin/env bash
set -euo pipefail
case "${{1:-}}" in
  ready)
    cat {ready_file}
    ;;
  *)
    echo "unsupported tk mock command: $1" >&2
    exit 1
    ;;
esac
""",
    )

    _write_executable(
        bin_dir / "pi",
        f"""#!/usr/bin/env bash
set -euo pipefail
printf 'CMD=%s\n' "$*" >> {pi_log}
printf 'PI_TK_INTERACTIVE_CHILD=%s\n' "${{PI_TK_INTERACTIVE_CHILD:-}}" >> {pi_log}
""",
    )

    return bin_dir, ready_file, pi_log


def test_dry_run_uses_tf_implement_command(tmp_path: Path) -> None:
    bin_dir, _, _ = _make_mock_bin(tmp_path, "ptf-123 Example ticket\n")
    state_dir = tmp_path / "state"

    result = subprocess.run(
        [str(SCRIPT), "--dry-run", "--once", "--clarify"],
        capture_output=True,
        text=True,
        env={
            **os.environ,
            "PATH": f"{bin_dir}:{os.environ['PATH']}",
            "TF_RALPH_LOOP_STATE_DIR": str(state_dir),
            "TF_RALPH_LOOP_POLL_INTERVAL": "0",
        },
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert 'pi "/tf-implement ptf-123 --clarify"' in result.stdout
    assert "/tk-implement" not in result.stdout


def test_interactive_mode_does_not_leak_tf_implement_recursion_guard(tmp_path: Path) -> None:
    bin_dir, _, pi_log = _make_mock_bin(tmp_path, "ptf-456 Example ticket\n")
    state_dir = tmp_path / "state"

    result = subprocess.run(
        [str(SCRIPT), "--once", "--interactive"],
        capture_output=True,
        text=True,
        env={
            **os.environ,
            "PATH": f"{bin_dir}:{os.environ['PATH']}",
            "TF_RALPH_LOOP_STATE_DIR": str(state_dir),
            "TF_RALPH_LOOP_POLL_INTERVAL": "0",
        },
        check=False,
    )

    assert result.returncode == 0, result.stderr

    log_text = pi_log.read_text(encoding="utf-8")
    assert 'CMD=/tf-implement ptf-456 --interactive' in log_text
    assert 'PI_TK_INTERACTIVE_CHILD=1' not in log_text
