"""Package-surface consistency tests for pi-tk-flow.

These tests validate the shipped framework surface only:
- prompt files
- chain preset files
- package manifest entries
- key README references

They intentionally do not inspect self-hosting runtime artifacts under .tf/ or .tickets.
"""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
PROMPTS_DIR = ROOT / "prompts"
CHAINS_DIR = ROOT / "assets" / "chains"
AGENTS_DIR = ROOT / "assets" / "agents"
PACKAGE_JSON = ROOT / "package.json"
README = ROOT / "README.md"
MODEL_CONFIGURATION = ROOT / "MODEL-CONFIGURATION.md"
PACKAGE_SURFACE_DIRS = [
    ROOT / "prompts",
    ROOT / "assets",
    ROOT / "extensions",
    ROOT / "python",
    ROOT / "docs",
]
PACKAGE_SURFACE_ROOT_FILES = [
    ROOT / "README.md",
    ROOT / "AGENTS.md",
    ROOT / "PROJECT.md",
    ROOT / "CONTEXT-GUIDE.md",
    ROOT / "MODEL-CONFIGURATION.md",
    ROOT / "REFACTOR-SIMPLIFY-SPEC.md",
]
EXPECTED_DOC_COPIES = {
    "README.md",
    "AGENTS.md",
    "PROJECT.md",
    "CONTEXT-GUIDE.md",
    "MODEL-CONFIGURATION.md",
    "REFACTOR-SIMPLIFY-SPEC.md",
    "FRAMEWORK-ASSESSMENT-AND-ROADMAP.md",
}
TEXT_SUFFIXES = {".md", ".ts", ".py", ".json", ".toml"}


EXPECTED_PROMPTS = {
    "tf-bootstrap.md",
    "tf-init.md",
    "tf-brainstorm.md",
    "tf-plan.md",
    "tf-plan-check.md",
    "tf-plan-refine.md",
    "tf-ticketize.md",
    "tf-implement.md",
    "tf-refactor.md",
    "tf-simplify.md",
}

EXPECTED_CHAINS = {
    "tf-brainstorm.chain.md",
    "tf-plan.chain.md",
    "tf-plan-thorough.chain.md",
    "tf-plan-check.chain.md",
    "tf-plan-refine.chain.md",
    "tf-ticketize.chain.md",
    "tf-refactor.chain.md",
    "tf-simplify.chain.md",
    "tf-path-a.chain.md",
    "tf-path-b.chain.md",
    "tf-path-c.chain.md",
}


LEGACY_TF_WORKFLOW_COMMAND_RE = re.compile(r"/tk-(bootstrap|init|implement|brainstorm|plan|plan-check|plan-refine|ticketize|refactor|simplify)\b")
WRONG_TICKET_CLI_RE = re.compile(r"\btf (add-note|close|status)\b")


def iter_package_surface_files() -> list[Path]:
    files: list[Path] = []
    files.extend(PACKAGE_SURFACE_ROOT_FILES)
    for directory in PACKAGE_SURFACE_DIRS:
        for path in directory.rglob("*"):
            if path.is_file() and path.suffix in TEXT_SUFFIXES and "__pycache__" not in path.parts:
                files.append(path)
    return files


def test_expected_prompt_files_exist() -> None:
    actual = {p.name for p in PROMPTS_DIR.glob("*.md")}
    missing = EXPECTED_PROMPTS - actual
    assert not missing, f"Missing prompt files: {sorted(missing)}"



def test_expected_chain_files_exist() -> None:
    actual = {p.name for p in CHAINS_DIR.glob("*.chain.md")}
    missing = EXPECTED_CHAINS - actual
    assert not missing, f"Missing chain files: {sorted(missing)}"



def test_expected_docs_copies_exist() -> None:
    actual = {p.name for p in (ROOT / "docs").glob("*.md")}
    missing = EXPECTED_DOC_COPIES - actual
    assert not missing, f"Missing docs copies: {sorted(missing)}"



def shipped_commands() -> list[str]:
    return [
        "/tf-bootstrap",
        "/tf-init",
        "/tf-brainstorm",
        "/tf-plan",
        "/tf-plan-check",
        "/tf-plan-refine",
        "/tf-ticketize",
        "/tf-implement",
        "/tf-refactor",
        "/tf-simplify",
    ]



def test_readme_mentions_all_shipped_prompt_commands() -> None:
    readme = README.read_text(encoding="utf-8")
    for command in shipped_commands():
        assert command in readme, f"README missing command reference: {command}"



def test_readme_mentions_new_chain_presets() -> None:
    readme = README.read_text(encoding="utf-8")
    assert "tf-refactor.chain.md" in readme
    assert "tf-simplify.chain.md" in readme



def test_readme_links_to_docs_copies() -> None:
    readme = README.read_text(encoding="utf-8")
    assert "docs/PROJECT.md" in readme
    assert "docs/CONTEXT-GUIDE.md" in readme
    assert "docs/MODEL-CONFIGURATION.md" in readme
    assert "docs/REFACTOR-SIMPLIFY-SPEC.md" in readme
    assert "docs/FRAMEWORK-ASSESSMENT-AND-ROADMAP.md" in readme



def test_readme_model_mapping_covers_all_shipped_commands() -> None:
    readme = README.read_text(encoding="utf-8")
    for command in shipped_commands():
        assert command in readme, f"README model mapping or docs missing command: {command}"



def test_model_configuration_covers_all_shipped_commands() -> None:
    model_configuration = MODEL_CONFIGURATION.read_text(encoding="utf-8")
    for command in shipped_commands():
        assert command in model_configuration, f"MODEL-CONFIGURATION missing command: {command}"



def test_package_manifest_registers_prompts_and_extensions_only() -> None:
    package_data = json.loads(PACKAGE_JSON.read_text(encoding="utf-8"))
    pi_config = package_data["pi"]

    assert pi_config["prompts"] == ["./prompts"]
    assert pi_config["extensions"] == ["./extensions"]
    assert "skills" not in pi_config, "package.json should not register a missing ./skills directory"



def test_deprecated_planner_agent_removed() -> None:
    assert not (AGENTS_DIR / "planner.md").exists()



def test_refactor_and_simplify_prompts_reference_project_context() -> None:
    refactor_prompt = (PROMPTS_DIR / "tf-refactor.md").read_text(encoding="utf-8")
    simplify_prompt = (PROMPTS_DIR / "tf-simplify.md").read_text(encoding="utf-8")

    for content in (refactor_prompt, simplify_prompt):
        assert "PROJECT.md" in content
        assert "AGENTS.md" in content
        assert ".tf/knowledge" in content



def test_refactor_and_simplify_chain_presets_use_specialist_agents() -> None:
    refactor_chain = (CHAINS_DIR / "tf-refactor.chain.md").read_text(encoding="utf-8")
    simplify_chain = (CHAINS_DIR / "tf-simplify.chain.md").read_text(encoding="utf-8")

    assert "## refactorer" in refactor_chain
    assert "## simplifier" in simplify_chain



def test_no_wrong_ticket_cli_namespace_in_package_surface() -> None:
    violations: list[str] = []

    for path in iter_package_surface_files():
        content = path.read_text(encoding="utf-8")
        for match in WRONG_TICKET_CLI_RE.finditer(content):
            line_number = content[: match.start()].count("\n") + 1
            line = content.splitlines()[line_number - 1]

            # Allow retrospective documentation that explicitly names the old wrong commands.
            if path.name == "FRAMEWORK-ASSESSMENT-AND-ROADMAP.md" and "wrong `tf add-note` / `tf close` / `tf status`" in line:
                continue

            violations.append(f"{path.relative_to(ROOT)}:{line_number}: {match.group(0)}")

    assert not violations, "Wrong ticket CLI namespace found:\n" + "\n".join(violations)



def test_no_legacy_tk_prefixed_workflow_commands_in_package_surface() -> None:
    violations: list[str] = []

    for path in iter_package_surface_files():
        content = path.read_text(encoding="utf-8")
        for match in LEGACY_TF_WORKFLOW_COMMAND_RE.finditer(content):
            line_number = content[: match.start()].count("\n") + 1
            line = content.splitlines()[line_number - 1]

            # Allow the README migration note in root and docs copies that explicitly documents the rename.
            if path.name == "README.md" and "/tk-bootstrap" in line and "legacy" in line.lower():
                continue

            violations.append(f"{path.relative_to(ROOT)}:{line_number}: {match.group(0)}")

    assert not violations, "Legacy /tk-* workflow command references found:\n" + "\n".join(violations)
