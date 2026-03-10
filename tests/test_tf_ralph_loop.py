"""Tests for the tf Ralph loop CLI wrapper."""

from __future__ import annotations

from types import SimpleNamespace

from pi_tk_flow_ui.__main__ import run_ralph
from pi_tk_flow_ui import tf_ralph_loop


class TestTfRalphLoop:
    """Behavior tests for the Ralph loop wrapper."""

    def test_main_forwards_explicit_argv(self, monkeypatch):
        """Explicit argv should be forwarded to the shell wrapper verbatim."""
        captured = {}

        def fake_call(cmd):
            captured["cmd"] = cmd
            return 0

        monkeypatch.setattr(tf_ralph_loop.subprocess, "call", fake_call)

        exit_code = tf_ralph_loop.main(["--dry-run", "--once"])

        assert exit_code == 0
        assert captured["cmd"][0].endswith("tf-ralph-loop.sh")
        assert captured["cmd"][1:] == ["--dry-run", "--once"]

    def test_run_ralph_builds_cli_flags(self, monkeypatch):
        """Unified tf CLI should translate argparse flags into shell args."""
        captured = {}

        def fake_main(argv=None):
            captured["argv"] = argv
            return 0

        monkeypatch.setattr(tf_ralph_loop, "main", fake_main)

        args = SimpleNamespace(
            clarify=True,
            hands_free=False,
            dispatch=True,
            interactive=False,
            dry_run=True,
            once=True,
            verbose=False,
            version=False,
        )

        exit_code = run_ralph(args)

        assert exit_code == 0
        assert captured["argv"] == ["--clarify", "--dispatch", "--dry-run", "--once"]
