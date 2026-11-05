English | **[简体中文](README.md)**

# ManualGen v6.3.3 — Operation Manual and User Manual Generator

## Six-layer progressive skeleton growth + knowledge-graph weaving + incremental backfill

**Positioning**: this is not "translating code into documentation". It understands the business like a product manager, walks the flows like a user, settles the details like an operations engineer, and finally emits a genuinely detailed **user operation manual** that traces back to source-code lines.

---

## Key capabilities

| Capability | Description |
| --- | --- |
| **Six-layer progressive extraction** | L0 skeleton → L1 module → L2 area → L3 feature → L4 operation → L5 detail, grown layer by layer, never skipping a layer |
| **Knowledge-graph driven** | 8 node types (MODULE / PAGE / REGION / FUNCTION / ENTITY / ROLE / ELEMENT / STEP) plus 20+ relation predicates build a business semantic network |
| **Snake cross-module chains** | Standalone chapters with Mermaid flowcharts describing end-to-end business flows, so you do not have to flip across four modules to follow one process |
| **Evidence traceability and confidence** | Every feature node carries at least one locatable source-code reference (path + line range); multiple nodes from the same source are merged as cross-validation; low-confidence nodes are flagged rather than written up as fact |
| **Incremental backfill** | New modules or code changes trigger local correction only — the whole project is not re-run |
| **Resumable runs** | Each batch is written to disk immediately with a JSON baton updated; close the conversation and pick up next time |
| **Hands-off orchestration** | An 18-stage state machine advances autonomously with AI self-review, so a usable manual comes out even with zero configuration |

---

## Architecture highlights (v6 vs v5)

| Dimension | ManualGen v6 | ManualGen v5 (older) |
| --- | --- | --- |
| Information architecture | Six-layer incremental + knowledge graph (not flat markdown) | Read everything at once + flat markdown |
| Stages | 18 (including AUTO_REVIEW self-audit) | 13 (including CONFIRM requiring user input) |
| Agents | 11 specialised agents collaborating | 7 agents |
| Cross-module flows | Snake concept chains in standalone chapters + end-to-end Mermaid | Modules isolated, no linkage |
| Evidence mechanism | At least one evidence item per feature node + reverse index to source lines; same-source auto-merge as cross-validation | Text output only, no evidence retained |
| Low-confidence handling | AI adjudicates autonomously with a warning (never writes a fabricated operation) | Asks the user to confirm one by one |
| Context strategy | Chunks loaded on demand by stage, batch and section | All chunks read at once |
| Resume granularity | Atomic write per batch, stop and resume any time | Write per stage; stopping mid-stage loses work |
| Project size ceiling | Unlimited (divide-and-conquer batching + incremental backfill) | Context overflow on large projects |
| Hands-off orchestration | Runs to DONE automatically once activated | Frequently interrupts to ask the user |

---

## Quick start (30 seconds)

ManualGen v6 is **fully orchestrated** and needs no configuration. The three most common ways to start are below — copy, paste, done.

### Trigger 1: write a complete manual from scratch (most common)

```
Generate the full user operation manual for the project at E:\my-erp,
aimed at operations and customer-support staff.
```

→ The AI starts the L0 skeleton → … → and writes `my-erp 用户操作手册.md` into the project root. A large ERP (30+ pages) typically takes 20–30 minutes, and can be resumed if the conversation is closed midway.

### Trigger 2: cover only key modules and key business flows

```
Focus on the "customer management", "order management" and "finance collection"
modules of E:\my-erp, and highlight the full end-to-end flow from customer order
to finance collection to shipment tracking.
```

→ Because the user **explicitly named the module scope**, the AI enters "core-priority mode" (off by default): the named modules are written in full from L0 to L5, and the rest are scanned to L2 as background and listed in Appendix F (uncovered modules). If no scope is named, it defaults to full coverage.

### Trigger 3: only backfill what changed

```
I added a "smart suggestions" module to E:\my-erp — please add that part to the
existing manual.
```

→ The AI takes the incremental-backfill path: scan only the new module L1 → L2 → …, rebuild the graph locally, append only the new chapter, and leave existing content untouched.

> Say "progress" or "pause" at any time to check in; say "continue" or just ignore it and it keeps running.

---

## When to use it, when not to

| Use it for | Do not use it for |
| --- | --- |
| Writing an operation manual for a large project from scratch (recommended) | One-off simple questions (just ask the AI) |
| Large codebases needing incremental extraction | Pure coding tasks (writing code, fixing bugs) |
| End-to-end cross-module flow documentation (Snake) | One-line summaries |
| Field-, button- and permission-level detail (L5) | — |
| Depth over summary, with evidence traceability | — |
| Zero-configuration hands-off generation (18 stages, AI autonomous) | — |

---

## Directory layout

```
ManualGen/
├── SKILL.md                 # Entry (18 stages / machine validation / FAQ index)
├── README.md                # This file (Chinese)
├── README.en.md             # This file (English)
├── manualgen_tools/         # v6.3 hard-validation layer (CLI machine verdicts the AI cannot bypass)
│   └── run.py               # 12 actions: verify/scan_tech/scan_flowcharts/check_deliverables/
│                            #   coverage/check_evidence/normalize_evidence/check_depth/
│                            #   check_reports/baton_fix/reset/ping
├── tests/                   # Regression tests (23 cases)
├── SKILL.chunks/            # Stage-sliced chunks 01–09 + loading matrix
├── agents/                  # 15 agent files (11 specialised + 4 v5-compatible/legacy)
├── protocols/               # Baton, graph, phase, progress and TODO protocols
├── knowledge-base/          # Context management, layered architecture, graph schema
├── templates/               # Manual structure, flowchart spec, appendix templates B–F
├── references/              # Anti-patterns, deep FAQ (21 questions)
├── quality-control/         # Quality system aligned with AUDIT
├── privacy/privacy-notice.md
├── 1-manifest/skill-manifest.yaml
└── CHANGELOG.md
```

---

## Version history

| Version | Date | Highlights |
| --- | --- | --- |
| v6.3.3 | 2026-10-19 | Exception-path hardening: added `check_reports` (blocks hollow AUDIT/JUDGE/REFINE/GAP reports), `verify` validates graph JSON integrity (half-written crashes), `scan_tech` supports `allow_terms` business whitelists and appendix E title aliases, `ping` checks Python ≥3.8; concurrency ban added; regression suite grown to 23 cases including failure drills |
| v6.3.2 | 2026-10-19 | Evidence-chain closure: added `check_evidence` (path/line/FUNCTION evidence at L1–L3 exits) and `normalize_evidence` (deterministic `path:line` normalisation into graph evidence and node index, no hand-writing by the AI); L4 references switched to node IDs, atomic exemption rules; `check_depth` supports pre- and post-graph modes; AUDIT adds sampled evidence review; suite grown to 21 cases |
| v6.3.1 | 2026-10-19 | Gate wiring: `verify` adds batch consistency (total present, done == total), `baton_fix` writes only completed and treats total as read-only, `coverage` tightened to whole-word matching, new `check_depth` (step count, flowcharts, EVD references, evidence parseability and line numbers); controller and chunk-07 wired to machine validation; 11 regression tests added |
| v6.3.0 | 2026-08-11 | CLI hard-validation layer: `manualgen_tools/run.py` takes over artefact, counting, technical-leakage, flowchart and coverage validation (8 actions); gates become dual-track machine + AI; baton counts can no longer be hand-filled; AUDIT blocking items fully scripted |
| v6.2.0 | 2026-08-11 | Fully autonomous orchestration: AUTO_REVIEW replaces CONFIRM, module-level JUDGE rejections, AUDIT with 10 dimensions plus an 11th coverage hard gate, unified artefact paths, appendix B–F templates, Refiner/Judge agents added |
| v6.0.0 | 2026-08-10 | Six-layer incremental + knowledge graph + Snake + incremental backfill; stages 13 → 18 |

---

## License

CC-BY-SA 4.0
