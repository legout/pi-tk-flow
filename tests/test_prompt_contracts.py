"""Semantic prompt-contract tests for the shipped pi-tk-flow framework surface."""

from __future__ import annotations

import re
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parent.parent
PROMPTS_DIR = ROOT / "prompts"
README = ROOT / "README.md"
MODEL_CONFIGURATION = ROOT / "MODEL-CONFIGURATION.md"
TF_BOOTSTRAP_EXTENSION = ROOT / "extensions" / "tf-bootstrap.ts"

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
MAPPING_ROW_RE = re.compile(r"\|\s*`(?P<command>/tf-[^`]+)`\s*\|\s*`(?P<model>[^`]+)`\s*\|\s*`(?P<thinking>[^`]+)`\s*\|")


PROMPT_TO_COMMAND = {
    "tf-bootstrap.md": "/tf-bootstrap",
    "tf-init.md": "/tf-init",
    "tf-brainstorm.md": "/tf-brainstorm",
    "tf-plan.md": "/tf-plan",
    "tf-plan-check.md": "/tf-plan-check",
    "tf-plan-refine.md": "/tf-plan-refine",
    "tf-ticketize.md": "/tf-ticketize",
    "tf-implement.md": "/tf-implement",
    "tf-refactor.md": "/tf-refactor",
    "tf-simplify.md": "/tf-simplify",
}


EXPECTED_FLAG_SETS = {
    "tf-init.md": {"--greenfield", "--brownfield", "--from", "--dry-run", "--no-overwrite"},
    "tf-implement.md": {"--async", "--clarify", "--interactive", "--hands-free", "--dispatch"},
    "tf-refactor.md": {"--from", "--scope", "--fast", "--thorough", "--preserve-api", "--prepare-for", "--async", "--clarify"},
    "tf-simplify.md": {"--from", "--scope", "--fast", "--thorough", "--hotspots-only", "--max-function-lines", "--async", "--clarify"},
}


EXPECTED_ARTIFACTS = {
    "tf-implement.md": {"anchor-context.md", "close-summary.md", "review-post-fix.md"},
    "tf-refactor.md": {"anchor-context.md", "plan.md", "implementation.md", "review.md", "test-results.md", "fixes.md", "review-post-fix.md", "close-summary.md"},
    "tf-simplify.md": {"anchor-context.md", "plan.md", "implementation.md", "review.md", "test-results.md", "fixes.md", "review-post-fix.md", "close-summary.md"},
}


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")



def parse_frontmatter(path: Path) -> dict:
    content = read_text(path)
    match = FRONTMATTER_RE.match(content)
    assert match, f"Missing YAML frontmatter: {path}"
    return yaml.safe_load(match.group(1)) or {}



def parse_mapping_table(text: str) -> dict[str, tuple[str, str]]:
    return {m.group("command"): (m.group("model"), m.group("thinking")) for m in MAPPING_ROW_RE.finditer(text)}



def test_prompt_frontmatter_models_match_documented_mapping() -> None:
    readme_mapping = parse_mapping_table(read_text(README))
    model_doc_mapping = parse_mapping_table(read_text(MODEL_CONFIGURATION))

    for prompt_name, command in PROMPT_TO_COMMAND.items():
        frontmatter = parse_frontmatter(PROMPTS_DIR / prompt_name)
        assert "model" in frontmatter, f"Prompt missing model frontmatter: {prompt_name}"
        assert "thinking" in frontmatter, f"Prompt missing thinking frontmatter: {prompt_name}"

        prompt_pair = (str(frontmatter["model"]), str(frontmatter["thinking"]))
        assert readme_mapping.get(command) == prompt_pair, f"README model mapping mismatch for {command}"
        assert model_doc_mapping.get(command) == prompt_pair, f"MODEL-CONFIGURATION mismatch for {command}"



def test_tf_bootstrap_prompt_and_extension_are_aligned() -> None:
    prompt_text = read_text(PROMPTS_DIR / "tf-bootstrap.md")
    extension_text = read_text(TF_BOOTSTRAP_EXTENSION)
    readme = read_text(README)

    assert 'pi.registerCommand("tf-bootstrap"' in extension_text
    assert "Run tf-bootstrap with `$@` args." in prompt_text
    assert "/tf-bootstrap" in readme



def test_tf_init_prompt_defines_required_project_context_outputs() -> None:
    prompt_text = read_text(PROMPTS_DIR / "tf-init.md")

    for required in [
        "PROJECT.md",
        "AGENTS.md",
        ".tf/AGENTS.md",
        ".tf/knowledge/README.md",
        ".tf/knowledge/baselines/coding-standards.md",
        ".tf/knowledge/baselines/testing.md",
        ".tf/knowledge/baselines/architecture.md",
        "<!-- PI-TK-FLOW:START -->",
        "<!-- PI-TK-FLOW:END -->",
        "Project-specific guidance",
        "greenfield",
        "brownfield",
        "/tf-init",
    ]:
        assert required in prompt_text, f"Missing tf-init contract piece: {required}"



def test_expected_flags_are_present_in_major_workflow_prompts() -> None:
    for prompt_name, flags in EXPECTED_FLAG_SETS.items():
        prompt_text = read_text(PROMPTS_DIR / prompt_name)
        for flag in flags:
            assert flag in prompt_text, f"Missing flag {flag} in {prompt_name}"



def test_expected_artifacts_are_present_in_major_workflow_prompts() -> None:
    for prompt_name, artifacts in EXPECTED_ARTIFACTS.items():
        prompt_text = read_text(PROMPTS_DIR / prompt_name)
        for artifact in artifacts:
            assert artifact in prompt_text, f"Missing artifact {artifact} in {prompt_name}"



def test_tf_implement_retains_interactive_router_contract() -> None:
    prompt_text = read_text(PROMPTS_DIR / "tf-implement.md")

    for required in [
        "PI_TK_INTERACTIVE_CHILD",
        '"mode": "interactive"',
        '"mode": "hands-free"',
        '"mode": "dispatch"',
        "session.json",
        "review-post-fix.md",
        "tk add-note",
        "tk close",
        "tk status",
    ]:
        assert required in prompt_text, f"Missing tf-implement interactive/router contract piece: {required}"



def test_tf_refactor_and_tf_simplify_define_ticket_and_goal_modes() -> None:
    for prompt_name in ["tf-refactor.md", "tf-simplify.md"]:
        prompt_text = read_text(PROMPTS_DIR / prompt_name)
        for required in [
            "Ticket mode",
            "Goal mode",
            "tf-closer",
            '"agent": "documenter"',
            "close-summary.md",
            "PROJECT.md",
            "AGENTS.md",
            ".tf/knowledge",
        ]:
            assert required in prompt_text, f"Missing {required} in {prompt_name}"



def test_refactor_and_simplify_ticket_mode_use_tk_not_tf_for_ticket_mutations() -> None:
    for prompt_name in ["tf-refactor.md", "tf-simplify.md"]:
        prompt_text = read_text(PROMPTS_DIR / prompt_name)
        assert "tk status" in prompt_text
        assert "tf add-note" not in prompt_text
        assert "tf close" not in prompt_text
        assert "tf status" not in prompt_text



def test_refactor_and_simplify_require_specialist_agents_in_prompt_logic() -> None:
    refactor_text = read_text(PROMPTS_DIR / "tf-refactor.md")
    simplify_text = read_text(PROMPTS_DIR / "tf-simplify.md")

    assert "refactorer" in refactor_text
    assert "simplifier" in simplify_text
    assert "plan-fast" in refactor_text and "plan-deep" in refactor_text
    assert "plan-fast" in simplify_text and "plan-deep" in simplify_text



def test_knowledge_persistence_uses_canonical_topic_filenames() -> None:
    plan_text = read_text(PROMPTS_DIR / "tf-plan.md")
    brainstorm_text = read_text(PROMPTS_DIR / "tf-brainstorm.md")
    refine_text = read_text(PROMPTS_DIR / "tf-plan-refine.md")

    assert "<KNOWLEDGE_TOPIC_DIR>/research.md" in plan_text
    assert "<KNOWLEDGE_TOPIC_DIR>/library-research.md" in plan_text
    assert "<KNOWLEDGE_TOPIC_DIR>/research.md" in brainstorm_text
    assert "<KNOWLEDGE_TOPIC_DIR>/library-research.md" in brainstorm_text
    assert "<KNOWLEDGE_TOPIC_DIR>/implementation-plan.md" in refine_text
    assert "<KNOWLEDGE_TOPIC_DIR>/refinement-summary.md" in refine_text

    for deprecated in [
        "plan-research.md",
        "brainstorm-research.md",
        "plan-library-research.md",
        "brainstorm-library-research.md",
        "implementation-plan-refined.md",
        "plan-refinement-summary.md",
    ]:
        assert deprecated not in plan_text
        assert deprecated not in brainstorm_text
        assert deprecated not in refine_text



def test_no_flat_topic_file_paths_in_package_prompts() -> None:
    for prompt_name in [
        "tf-init.md",
        "tf-implement.md",
        "tf-plan.md",
        "tf-brainstorm.md",
        "tf-plan-check.md",
        "tf-plan-refine.md",
        "tf-refactor.md",
        "tf-simplify.md",
    ]:
        prompt_text = read_text(PROMPTS_DIR / prompt_name)
        assert ".tf/knowledge/topics/<topic-slug>.md" not in prompt_text, f"Flat topic file path found in {prompt_name}"
