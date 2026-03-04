# Ticketize Summary

## Tickets Created
| Key | Ticket ID | Title | Type | Priority |
| --- | --- | --- | --- | --- |
| Epic | ptf-it5r | Add per-command model configuration via pi-prompt-template-model | epic | 1 |
| S1 | ptf-cb32 | Publish canonical README model mapping and extension behavior | feature | 1 |
| S2 | ptf-62c4 | Apply prompt frontmatter model defaults across tk prompts | feature | 1 |
| S3 | ptf-cgx4 | Document canonical 5-level model precedence and subagent behavior | feature | 2 |
| S4 | ptf-vzfu | Run validation checklist and capture pass/fail evidence | task | 2 |

All slice tickets are parented to epic `ptf-it5r`.

## Dependency Links
- `ptf-62c4` depends on `ptf-cb32`
- `ptf-cgx4` depends on `ptf-cb32`
- `ptf-vzfu` depends on `ptf-62c4`
- `ptf-vzfu` depends on `ptf-cgx4`

`tk dep cycle` result: **No dependency cycles found**.

## Commands Executed
```bash
tk create "Add per-command model configuration via pi-prompt-template-model" \
  --type epic \
  --priority 1 \
  --tags planning,model-configuration,tk-flow \
  --description "Align tk-flow command defaults, precedence documentation, and validation evidence so per-command model behavior is consistent, documented, and safely verifiable with and without the optional extension." \
  --design "Source docs: .tf/plans/2026-03-04-default-models-for-commands/{01-prd.md,02-spec.md,03-implementation-plan.md,07-refinement-summary.md}." \
  --acceptance "- [ ] README contains canonical command→model mapping including /tk-bootstrap.
- [ ] Prompt-backed tk commands carry aligned model frontmatter defaults.
- [ ] Knowledge base defines canonical 5-level precedence and subagent behavior.
- [ ] Validation evidence confirms extension-on and extension-off behavior without regressions."

tk create "Publish canonical README model mapping and extension behavior" \
  --type feature \
  --parent ptf-it5r \
  --priority 1 \
  --tags feature,vertical-slice,documentation,model-configuration \
  --description "Update README with optional pi-prompt-template-model guidance and one authoritative command→model mapping table including /tk-bootstrap." \
  --design "Refs: PRD Solution + ID-1/ID-2; Spec Components §2; Implementation Plan Task 1." \
  --acceptance "- [ ] README includes extension install instructions and behavior notes (switch, fallback, restore).
- [ ] Mapping table includes all required commands, including /tk-bootstrap → claude-haiku-4-5.
- [ ] README states commands still execute normally when extension is not installed.
- [ ] Mapping is presented as canonical source for prompt/docs alignment."

tk create "Apply prompt frontmatter model defaults across tk prompts" \
  --type feature \
  --parent ptf-it5r \
  --priority 1 \
  --tags feature,vertical-slice,prompts,model-configuration \
  --description "Add model frontmatter to all six prompt-backed tk commands and add thinking only where materially useful, keeping prompt body logic unchanged." \
  --design "Refs: PRD US-1/US-2 + ID-2/ID-3; Spec Components §1; Implementation Plan Task 2." \
  --acceptance "- [ ] prompts/tk-implement.md has model: claude-haiku-4-5, claude-sonnet-4-20250514.
- [ ] prompts/tk-brainstorm.md, prompts/tk-plan.md, and prompts/tk-plan-refine.md use model: claude-sonnet-4-20250514.
- [ ] prompts/tk-plan-check.md and prompts/tk-ticketize.md use model: claude-haiku-4-5.
- [ ] All six files keep valid YAML frontmatter; prompt bodies remain semantically unchanged."

tk create "Document canonical 5-level model precedence and subagent behavior" \
  --type feature \
  --parent ptf-it5r \
  --priority 2 \
  --tags feature,vertical-slice,knowledge-base,model-configuration \
  --description "Create .tf/knowledge/topics/model-configuration.md with the exact precedence ladder and examples that separate main-loop prompt model selection from subagent runtime overrides, then cross-link from README." \
  --design "Refs: PRD US-4/US-5 + ID-4; Spec Components §3; Implementation Plan Task 3." \
  --acceptance "- [ ] New knowledge topic exists at .tf/knowledge/topics/model-configuration.md.
- [ ] The 5-level precedence ladder appears verbatim in required order.
- [ ] Examples distinguish subagent tool call model overrides from main-loop prompt-frontmatter model selection.
- [ ] README references the topic and contains no conflicting precedence text."

tk create "Run validation checklist and capture pass/fail evidence" \
  --type task \
  --parent ptf-it5r \
  --priority 2 \
  --tags task,vertical-slice,validation,model-configuration \
  --description "Execute static grep checks, extension-on runtime checks, and extension-off graceful degradation checks; record outputs and pass/fail decisions in 04-progress.md." \
  --design "Refs: PRD TD-1..TD-5; Spec Testing Strategy + Graceful Degradation; Implementation Plan Task 4 validation checklist." \
  --acceptance "- [ ] .tf/plans/2026-03-04-default-models-for-commands/04-progress.md records outputs for all required static checks.
- [ ] Extension-installed runtime checks are executed and switch/restore observations are logged.
- [ ] Extension-disabled/uninstalled run is executed and confirms commands still function without regression.
- [ ] PASS/FAIL outcomes are recorded against all required criteria."

tk dep ptf-62c4 ptf-cb32
tk dep ptf-cgx4 ptf-cb32
tk dep ptf-vzfu ptf-62c4
tk dep ptf-vzfu ptf-cgx4

tk dep cycle
```

## Command Output Snapshot
- `tk dep ptf-62c4 ptf-cb32` → `Added dependency: ptf-62c4 -> ptf-cb32`
- `tk dep ptf-cgx4 ptf-cb32` → `Added dependency: ptf-cgx4 -> ptf-cb32`
- `tk dep ptf-vzfu ptf-62c4` → `Added dependency: ptf-vzfu -> ptf-62c4`
- `tk dep ptf-vzfu ptf-cgx4` → `Added dependency: ptf-vzfu -> ptf-cgx4`
- `tk dep cycle` → `No dependency cycles found`
