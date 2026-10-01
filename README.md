# DEVWORKS Harness

> 🇧🇷 [Documentação em português](README.pt-BR.md)

A standalone harness that takes a project from idea to implementation through
specification, release planning, executable tasks, and mechanically validated
execution. It works with Codex, Claude Code, OpenCode, and Antigravity; the
Claude plugin remains only as a backward-compatible adapter.

The harness is **stack-agnostic**: language, framework, commands, and conventions are defined by the project's own documents (`AGENTS.md`, `CLAUDE.md`, the `.spec/` chain), never by the harness.

## Workflow overview

```
 IDEA                                              CODE
   │                                                 ▲
   ▼                                                 │
 init ────────────────────────► .spec/init/          │
 (PRD, stories, suggested       release map)         │
   │                                                 │
   │            plan ─► SPEC.md + PLAN.md             │
   │            task-builder ─► one-phase PHASES.md   │
   ▼                                                 │
one-phase PHASES.md ──────────────────────► scripts/ralph.sh
                                            (autonomous execution
                                             with 4 gates)

 /ai-context ─► AGENTS.md + docs/agents/*  (documents the ALREADY implemented
                                            code; feeds /plan and ralph)
```

Four workflows that fit together:

1. **`init`** — turns a PRD into initial project context (description → stories → suggested schema → release map).
2. **`plan`** — turns a feature description into a formal SPEC and release map.
3. **`task-builder`** — turns an approved release into small tasks and creates a one-phase `PHASES.md`.
4. **`ralph.sh`** — executes any phase document autonomously, one fresh agent session per phase, with mechanical gates; changes remain available for manual review and commit.

Cross-cutting: **`/ai-context`** keeps the context tree (`AGENTS.md`, `CLAUDE.md`, `docs/agents/*.md`) in sync with the real code.

## Current state and recommended flow

The four canonical Skills live in `skills/` and can be installed for all four
engines. They produce the same artifacts; only the interface used to invoke a
Skill changes.

| Situation | Flow |
|---|---|
| New project | `init` with the PRD → `plan` → approve releases → `task-builder` for the next phase → Ralph → validate and commit |
| Legacy project | `ai-context` → review AS IS documentation → maintenance `plan` → `task-builder` → Ralph → regression validation and commit |

`plan` defines large release-like phases. `task-builder` details only the
selected phase and creates its own `PHASES.md`; this is the recommended
one-cycle-at-a-time workflow.

Ralph also accepts a document with multiple phases and runs them **sequentially**
in a fresh session per phase. It stops on the first failure by default;
`--keep-going` preserves partial work and continues. `--from N` starts at phase
N and continues with later phases - it does not execute only one phase.

## Installation

DEVWORKS Harness is standalone: keep this repository in any local directory
and invoke its scripts from the target project. It does not depend on a Claude
Code plugin, marketplace, or command namespace.

The canonical `init`, `plan`, `task-builder`, and `ai-context` Skills live in
`skills/`. The installer copies identical content to each engine's discovery
directory; it stores no tokens and needs no target-project dependency:

```bash
scripts/install-platform.sh --platform codex --scope project
scripts/install-platform.sh --platform claude --scope project
scripts/install-platform.sh --platform opencode --scope user
scripts/install-platform.sh --platform antigravity --scope project
```

See [the cross-platform workflow contract](docs/agents/canonical-workflows.md).

`ralph.sh` is a standalone bash script — copy or reference `scripts/ralph.sh` and run it directly in the target project's repository.

### Installation destinations

| Engine | Project | User |
|---|---|---|
| Codex | `.agents/skills/` | `~/.codex/skills/` |
| Claude Code | `.claude/skills/` | `~/.claude/skills/` |
| OpenCode | `.opencode/skills/` | `~/.config/opencode/skills/` |
| Antigravity | `.agents/skills/` | `~/.gemini/config/skills/` |

Use `--check` to validate the CLI and destination without copying files. A
regular installation requires an authenticated CLI and validates all four
Skills before writing.

## What's new: DEVWORKS, multi-agent workflows, and observability

The harness now has a vendor-neutral execution core. The stable `init`,
`plan`, `task-builder`, and `ai-context` workflows keep the same output
contracts. The Claude plugin preserves its legacy commands, but is not the
canonical source or a dependency of the other engines:

```text
.spec/init/*
.spec/features/<slug>/*
AGENTS.md, CLAUDE.md, and docs/agents/*
PHASES.md executable by Ralph
```

The installer below is the single distribution path. `--check` validates the
CLI and destination without copying files; a regular installation validates all
four Skills before creating any directory:

```bash
scripts/install-platform.sh --platform codex --scope project
scripts/install-platform.sh --platform claude --scope project
scripts/install-platform.sh --platform opencode --scope user
scripts/install-platform.sh --platform antigravity --scope project
```

Each execution has a `run-YYYYMMDD-HHMMSS-PID` ID, retained in
`.phases/runs/<run-id>/`; hash-keyed progress supports safe continuation and a
repository lock prevents concurrent Ralphs.

### Initial model policy

`config/model-policy.tsv` centralizes the Antigravity model policy. Ralph
automatically applies execution and verification profiles; for `plan` and
`task-builder`, choose the matching route in the engine interface.

| Role | Primary | Fallbacks |
|---|---|---|
| Plan and Task Builder | Claude Opus 4.6 Thinking | Gemini 3.1 Pro High → Gemini 3.8 Flash High |
| `routine` execution | Gemini 3.8 Flash Medium | Flash High → Pro High |
| `standard` execution | Gemini 3.8 Flash High | Pro High → Claude Opus |
| `complex` execution | Gemini 3.1 Pro High | Claude Opus → Flash High |
| Verification | Claude Sonnet 4.6 | Gemini 3.8 Flash High |

When an Antigravity model reaches its usage limit, Ralph moves to the next
model in the route and resumes the same phase. A failed test or red gate starts
a regular fix cycle; it does not automatically switch models.

The read-only web monitor complements `ralph-watch.sh`:

```bash
./scripts/ralph-web.sh /path/to/project
# http://127.0.0.1:7331
```

It uses Python 3 and static HTML/CSS/JavaScript, binds only to loopback, and
offers versioned run/history/log APIs without CORS or control endpoints. See
the Portuguese [DEVWORKS Ralph guide](output/pdf/guia-devworks-ralph.pdf) for
operational workflows.

**ralph.sh prerequisites:**

- Codex engine: `npm install -g @openai/codex`
- Claude engine: `npm install -g @anthropic-ai/claude-code`
- OpenCode engine: stable `opencode` CLI, installed and authenticated ([installation](https://opencode.ai/docs))
- Antigravity engine: `agy` CLI, installed and authenticated ([installation](https://antigravity.google/docs/cli/install/))
- Root of a git repository (used read-only by gate 1)

## Commands

### `/init` — init chain router

Shows the state of the `.spec/init/` artifacts (present / absent / stale) and **invokes the next command in the chain** (one hop per run — re-run `/init` to advance). Writes nothing itself; all authoring lives in the invoked `init:*` command.

The chain, in order:

| # | Artifact | Command | Inputs |
|---|---|---|---|
| 1 | `.spec/init/project-description.md` | `/init:project-description` | — (head of chain) |
| 2 | `.spec/init/user-stories.md` | `/init:user-stories` | project-description |
| 3 | `.spec/init/database-schema.md` | `/init:database-schema` | description + stories |
| 4 | `.spec/init/project-phases.md` | `/init:project-phases` | description + stories + schema |
| — | `.spec/init/design/` | manual (optional) | — |

Every generated artifact carries a **stamp** of its inputs on line 3 (`file@sha256:<12 chars>`). If an input changes later, `/init` detects it and reports the downstream artifact as *stale* — re-running the corresponding command is upsert-safe: it interviews only about the deltas and refreshes the stamp.

- **`/init:project-description`** — interviews the developer, discovers the stack, and produces a structured project description.
- **`/init:user-stories`** — derives structured, testable user stories from the description.
- **`/init:database-schema`** — derives a suggested database schema in DBML.
- **`/init:project-phases`** — plans the build into numbered, agent-ready phases with tasks, acceptance criteria, and feature tests. **This is `ralph.sh`'s default input.** Reads `.spec/init/design/` when present (screen/component refs).

### `/plan` — feature planning pipeline

The commands below document the legacy Claude plugin interface. In the
portable flow, the `plan` Skill creates `SPEC.md` and `PLAN.md`; after approval,
the `task-builder` Skill creates the selected release's `PHASES.md`.

```
/plan "<feature description or path to a description file>"
```

Produces, under `.spec/features/<slug>/`:

| Artifact | Content |
|---|---|
| `SPEC.md` | Formal specification in GEARS syntax, with RIGID/FLEXIBLE sections, AS IS / TO BE diagrams, and binary acceptance criteria |
| `PLAN.md` | Architecture-aware task decomposition with dependency phases, risks, and validation criteria |
| `PHASES.md` | Compatibility output of the Claude command; in the portable flow, `task-builder` creates it for one selected phase |
| `openapi.yaml` / `service.proto` / `asyncapi.yaml` | Formal contracts, when the SPEC declares an API surface (conditional) |

Key characteristics:

- **No issue tracker** — the confirmed description + ACs are the source of truth. No Jira.
- **Complexity tier** (`light` / `standard` / `complete`) classified from objective signals (requirement count, multi-repo, contracts, messaging); adjusts SPEC depth, whether the clarifier is mandatory, and contract emission.
- **Human checkpoints** at every step: confirmation of the normalized input, SPEC approval, ambiguity resolution, decomposition sign-off.
- **Two-phase clarifier** — the agent analyzes the SPEC and returns prioritized questions; the router presents them to the developer and re-invokes the agent with the answers, which updates the SPEC in-place.
- **Architecture gate** — requires `AGENTS.md` / `docs/agents/` (or warns and flags `architecture_reference_status: missing`). The pipeline never plans silently without architecture context.
- **Never writes application code.** The close-out points at the execution handoff:

```bash
./ralph.sh .spec/features/<slug>/PHASES.md
```

In the portable flow, pass Ralph the Task Builder output:

```bash
./scripts/ralph.sh .spec/features/<slug>/phases/<NN>-<name>/PHASES.md
```

### `/ai-context` — canonical context tree

```
/ai-context [path] [+id] [-id] [--adopt]
```

Generates or refreshes 10 artifacts from the **implemented code** (never reads `.spec/`):

| Artifact | Content |
|---|---|
| `AGENTS.md` | 6 sections: commands, conventions, behavioral rules, setup, references, docs index |
| `CLAUDE.md` | ≤ 400-byte redirect to AGENTS.md |
| `docs/agents/project_overview.md` | Purpose, consumers, macro flow |
| `docs/agents/architecture.md` | Style, layout, layer responsibilities |
| `docs/agents/tech_stack.md` | Language, framework, runtime, test tooling |
| `docs/agents/coding_guidelines.md` | ≥ 3 observed patterns + enforcement |
| `docs/agents/domain_rules.md` | Business rules as implemented |
| `docs/agents/api_contracts.md` | Endpoints, payloads, message formats |
| `docs/agents/data_model.md` | Entities, storage, migrations |
| `docs/agents/dependencies.md` | External services, internal libs, shared infra |

Core rules:

- **Idempotent** — safe upsert; re-running updates only what drifted.
- **Documents reality (AS IS)** — code, manifests, CI, and configs are the only sources; never invents, never prescribes.
- **Ownership contract** — every generated file carries a banner on line 3. A file without the banner (hand-written) is never clobbered; `--adopt` folds its concrete rules into the generated tree and takes ownership.
- **Preserves third-party blocks** — `<tag>...</tag>` regions (e.g. Laravel Boost) are re-appended verbatim on regeneration.
- `+id` / `-id` filters generate only a subset (e.g. `/ai-context +AGENTS +architecture`).

## `scripts/ralph.sh` — execution orchestrator

Reads a phase document, splits it on the `## Phase N: <title>` heading, and feeds each phase to a **fresh** Codex CLI, Claude Code, OpenCode, or Antigravity session, with no human interaction from start to finish. The commands, agents, and packaging in this repository remain Claude-plugin-only; Ralph itself is standalone.

For a Portuguese operational walkthrough, see [the four-engine Ralph guide](docs/guia-ralph-quatro-engines.md).

```bash
./scripts/ralph.sh [options] [path-to-file]
```

With no argument, the input resolves in this order: `.spec/init/project-phases.md` → `.spec/project-phases.md` (pre-init layout, with a warning). A feature `PHASES.md` is also valid input.

> **Autonomy and permissions note**: Ralph is an unattended orchestrator by design. Implementation sessions are autonomous: Codex uses `danger-full-access`, Claude uses `--dangerously-skip-permissions`, OpenCode uses `run --auto`, and Antigravity uses `accept-edits` with `--dangerously-skip-permissions`. Run it only in repositories you trust, ideally in a disposable branch or isolated environment (container/VM). Ralph never stages, commits, resets, or changes Git exclusion settings; review its accumulated diff and commit manually. Gate 3 is constrained: Codex is read-only; Claude allows only `Read,Glob,Grep`; OpenCode's inline configuration denies everything except read/glob/grep; Antigravity uses `--mode plan --sandbox`, without the dangerous flag.

### Invariants

1. Every phase **and** every fix cycle runs in a fresh session with a self-contained prompt. Sessions are never reused.
2. Zero questions — fully autonomous execution.
3. A phase is only "complete" when it passes the **4 mechanical gates**, never by the engine's exit code.
4. API usage limit → waits for the reset and re-runs the **same** phase, without consuming a fix cycle.
5. **No Git writes** — phases leave their changes in the working tree for manual review and commit.

### The 4 gates

| Gate | Question | How it decides |
|---|---|---|
| 0 | Did the engine actually finish? | codex: exit code; claude: successful result JSON; opencode: exit code 0, no terminal error event, and `step_finish`; antigravity: exit code 0 and final `result.status: SUCCESS` |
| 1 | Did the session write code? | Tree signature before/after. **A signal, not a verdict** — an already-implemented phase makes the engine (correctly) write nothing; the signal feeds the fix-cycle cause |
| 2 | Does the test suite pass? | Run **by ralph itself**, outside the agent session — the agent cannot "fake green" |
| 3 | Is each task actually in the code? | Independent restricted verifier session that emits `TASK <n>: DONE/INCOMPLETE` per task. Runs on every phase by default (`RALPH_VERIFY=always`); `RALPH_VERIFY_MODEL` optionally selects its model |

Any red gate → **fix cycle**: a fresh session receives the full phase + the real failure cause (never a generic "tests failed"). Default: 3 cycles per phase.

Green gates mark the phase done; its changes remain in the working tree.

### Test command detection (gate 2)

First rule that resolves wins: `--test-cmd` → `RALPH_TEST_CMD` → manifest detection (Laravel Sail → `composer test` → `php artisan test` → `npm test` → `pytest` → `go test ./...` → `cargo test`) → nothing resolved = gate 2 skipped with a loud warning (gate 3 holds the line alone).

Laravel Sail projects: the suite runs **inside the container** (`vendor/bin/sail test`); stopped containers abort at preflight — every gate 2 would fail and burn fix cycles for nothing.

### Options and variables

| Option | Effect |
|---|---|
| `--engine codex\|claude\|opencode\|antigravity` | Implementation engine (default: `codex`; Antigravity invokes `agy`) |
| `--profile routine\|standard\|complex` | Antigravity model-policy profile (default: `standard`) |
| `--from N` | Starts at phase N (clears progress for phases ≥ N) |
| `--keep-going` | Continues after a phase fails, preserving partial changes in the working tree (default: stop) |
| `--max-cycles N` | Fix cycles per phase (default: 3) |
| `--test-cmd "<cmd>"` | Project test command (gate 2) |
| `--no-verify` | Disables gate 3 |
| `--dashboard` | Live panel in the terminal (see below) |

| Variable | Effect |
|---|---|
| `RALPH_TEST_CMD` | Test command (gate 2) |
| `RALPH_VERIFY` | Gate 3: `always` (default) \| `auto` (saves tokens: only when gate 2's verdict isn't enough) \| `off` |
| `RALPH_VERIFY_MODEL` | Optional verifier model (`sonnet` is the Claude default) |
| `RALPH_EXECUTION_PROFILE` | Antigravity profile: `routine`, `standard`, or `complex` |
| `RALPH_IMPLEMENTATION_MODEL` | Pins one Antigravity model and disables model fallback |
| `RALPH_MODEL_POLICY` | Alternate path to the model-policy file |
| `RALPH_MAX_CYCLES` | Fix cycles per phase (default: 3) |
| `RALPH_MAX_LIMIT_WAITS` | Consecutive usage-limit waits, per phase (default: 20) |
| `RALPH_LIMIT_WAIT_DEFAULT` | Fallback wait in seconds (default: 1800) |
| `RALPH_LIMIT_BUFFER` | Extra seconds after the reset (default: 60) |
| `RALPH_ANTIGRAVITY_TIMEOUT` | `agy --print-timeout` per session (default: `30m`) |

During each session, ralph exports `RALPH_ENGINE`, `RALPH_PHASE_TITLE`, `RALPH_PHASE_NUM`, `RALPH_PHASE_TOTAL`, `RALPH_PHASE_ATTEMPT`, and `RALPH_PHASE_MAX_ATTEMPTS` — useful for notification hooks (e.g. n8n).

### State and progress

Internal work lives in `.phases/`: `current` points to the selected run,
`runs/<run-id>/` retains its phases, prompts, state, and logs, and
`progress/<input-hash>.progress` resumes only the same input. A compatible
legacy `.phases/.progress` is imported once. A repository lock prevents two
Ralph processes from executing concurrently.

Exit code: `0` = all phases green; `1` = some phase failed or aborted.

## `scripts/ralph-watch.sh` — live panel

ralph publishes run state to `.phases/state/` **always**, with or without `--dashboard`. `ralph-watch.sh` reads that state and draws the panel:

```bash
./scripts/ralph.sh --engine claude --dashboard   # panel in the same terminal
./scripts/ralph-watch.sh /path/to/repo           # panel from another terminal
```

```
┌─────────────────── PROGRESSO ───────────────────┐ ┌──────────────── TRABALHO ATUAL ─────────────────┐
│ Fases  1/2      [███████████░░░░░░░░░░░░]  50%  │ │ Fase:      2 · Interface observável             │
│ Tasks  1/2      [███████████░░░░░░░░░░░░]  50%  │ │ Ciclo:     1/3    Gate: G2                      │
└─────────────────────────────────────────────────┘ └─────────────────────────────────────────────────┘
┌──────┬────────────────────────────────────────────┬────────────────┬───────────┬─────────────────────┐
│ F2   │ Interface observável                       │ ▶ Em execução  │ 1         │ G0 ✓ G1 ✓ G2 ⋯ G3 · │
│ T1   │   ↳ renderizar títulos longos              │ ✓ Concluída    │ –         │ –                   │
│ T2   │   ↳ cobrir falhas de rede com retry        │ ▶ Em execução  │ –         │ –                   │
└──────┴────────────────────────────────────────────┴────────────────┴───────────┴─────────────────────┘
```

### Where per-task progress comes from

A phase is **one** agent session, so ralph could not know where the session is — unless the session says so. Claude, OpenCode, and Antigravity expose line-oriented output while they work:

Claude uses `--output-format stream-json`, OpenCode uses `run --format json`, and Antigravity uses `--output-format stream-json`. Ralph reads those streams and rewrites progress into `.phases/state/live.tsv`, from four sources, in this order of precedence:

1. **Text markers** (primary source). The prompt tells the agent to write, as a standalone line, `RALPH-TASK <n> START` before starting item *n* and `RALPH-TASK <n> DONE` once it is ready. It is plain text: it **depends on no tool at all** — which is what matters, because in a headless session (`claude -p`) task-list tools simply do not exist, even when the agent tries to load them via `ToolSearch`.
2. **The agent's task list**, when the session has one (`TaskCreate`/`TaskUpdate` or `TodoWrite`): its `in_progress`/`completed` transitions become progress.
3. **Observational fallback** — with no marker and no list, ralph infers from what the agent edits. A `/plan` plan declares `Arquivos:` on every item, and it is that match (edited path ↔ file declared by the task) that provides the granularity; without the declaration it falls back to the task's own text. On entering a task the earlier ones count as done — the agent works in order, and not every task has a file of its own.
4. **Sign of life**: as soon as the session opens, task 1 shows as running — never a whole phase frozen at "Pendente".

At the end of the phase, **gate 3 has the last word**: the verifier's `TASK <n>: DONE/INCOMPLETE` verdict overrides marker, list and inference alike. A task marked done but not in the code shows up as `! Incompleta`.

So: during the phase the panel shows the agent's intent; at the end of the phase it shows the verified truth.

On the **codex** engine there is no equivalent stream — granularity stays per phase, and tasks show as pending until gate 3's verdict.

### Large plans: pinned top, scrolling table

With dozens of tasks the table no longer fits on screen. The panel then keeps **the top pinned** (identification, bars, current work) and scrolls the phase/task table inside a window sized to the terminal — with a scrollbar on the right edge and a footer stating what fell outside:

```
  ▲ 23 above · ▼ 9 below · following the current phase · ↑↓ PgUp/PgDn scroll · f follows the phase
```

The running line — phase and task — is **highlighted end to end**, so it can be spotted at a glance in a full table.

By default the window **follows the current phase**: it shows the whole phase block when it fits, and centers the running task when it doesn't. The keys below take over at any time and also work under `--dashboard`, with the panel embedded in ralph:

| Key | Effect |
|---|---|
| `↑` `↓` or `k` `j` | Scrolls one line |
| `PgUp` `PgDn`, `b` or space | Scrolls one page |
| `Home`/`g` and `End`/`G` | First and last line |
| `f` | Goes back to following the current phase |
| `q` | Quits the panel (standalone mode only; does not stop ralph) |

| Watch option | Effect |
|---|---|
| `--once` | Draws one frame and exits (useful in scripts/CI); full dump, no clipping |
| `--interval N` | Seconds between frames (default: 1) |
| `--no-color` | Disables ANSI |
| `--color` | Forces ANSI even without a terminal (tests, files) |
| `RALPH_WATCH_COLS` | Pins the width, for terminals that don't report it |
| `RALPH_WATCH_LINES` | Pins the height; with `--once` it also enables the scrolling window |

With `--dashboard`, ralph's log lines go to `.phases/logs/ralph.log` (the panel owns the screen) and the final report prints to the terminal on exit. Without `ralph-watch.sh` next to `ralph.sh`, `--dashboard` warns and falls back to log mode — `ralph.sh` stays copyable on its own into another repository.

## `scripts/ralph-web.sh` — local web monitor

The read-only monitor shows current state and project history in a responsive,
terminal-inspired interface. It uses Python 3 plus static HTML/CSS/JavaScript,
listens only on loopback, and has no CORS or control endpoints.

```bash
./scripts/ralph-web.sh /path/to/repo
# Ralph Web: http://127.0.0.1:7331
```

JSON endpoints: `/api/v1/runs`, `/api/v1/runs/current`, `/api/v1/runs/{id}`
and `/api/v1/runs/{id}/logs?after=<offset>`.


### Input format contract

Validated at preflight:

- ≥ 1 heading `## Phase N: <title>`
- No `## Phase ...` heading outside that format (a malformed heading silently disappears from the run — preflight aborts before burning tokens)
- Sub-phases as `### Phase N.M:` (do not become their own session)
- Any other `## ` heading ends the previous phase's capture

## Agents

Commands are **thin routers** — all template knowledge lives in the agents:

| Agent | Pipeline | Role |
|---|---|---|
| `specifier` | `/plan` §5 | Confirmed description + ACs → formal SPEC.md (GEARS, RIGID/FLEXIBLE) |
| `clarifier` | `/plan` §6 | Adversarial requirements QA: finds ambiguities, resolves them with the developer's answers |
| `planner` | `/plan` §7 | Legacy Claude adapter: SPEC → PLAN.md + PHASES.md + contracts; read-only over the code |
| `ai-context-inspector` | `/ai-context` §3 | Read-only repo sweep → structured digest |
| `ai-context-core` | `/ai-context` §4 | Digest → `AGENTS.md` + `CLAUDE.md` |
| `ai-context-docs` | `/ai-context` §4 | Digest → the 8 `docs/agents/*.md` files |

The two `/ai-context` writers run in parallel (disjoint files, read-only digest).

## Repository structure

```
.claude-plugin/plugin.json     plugin manifest
commands/
  init.md                      /init (diagnostic router)
  init/                        /init:project-description, user-stories,
                               database-schema, project-phases
  plan.md                      /plan (planning pipeline router)
  ai-context.md                /ai-context (context tree router)
agents/                        specifier, clarifier, planner,
                               ai-context-{inspector,core,docs}
scripts/
  ralph.sh                     phase-by-phase execution orchestrator
  ralph-watch.sh               live run panel (reads .phases/state/)
  test-ralph.sh                red/green suite for ralph with a mock engine
  check-init-drift.sh          guards against textual drift of the rules
                               duplicated across the init commands
  check-shell.sh               bash -n + shellcheck over scripts/*.sh
docs/plans/                    internal hardening plans for the harness
```

## Development

```bash
scripts/test-ralph.sh        # ralph.sh suite — fake `claude`/`codex`/`opencode`/`agy` binaries
                             # on PATH, zero network, zero tokens; exit 0 = green
scripts/test-ralph.sh <case> # run a single case
scripts/check-shell.sh       # bash -n over all scripts + shellcheck when available
scripts/check-init-drift.sh  # verbatim anchors for the shared init:* rules
```

`test-ralph.sh` requires Bash 4+ (it uses associative arrays); macOS's system
Bash 3.2 is sufficient for `scripts/check-shell.sh`, but not for the functional
suite.

About `check-init-drift.sh`: the four `commands/init/*.md` files **intentionally inline** the same interview, language, re-run, and staleness rules — plugin commands must be self-contained at runtime (they execute inside the developer's project, where the plugin root is not reachable via `@`-includes). The cost of that duplication is silent drift; the script makes drift loud.

## Design principles

- **Thin routers, agents own the content** — commands orchestrate, verify artifacts on disk, and report; they never author SPEC/PLAN/docs.
- **Trust, but verify** — every artifact delivered by an agent is mechanically validated (existence, headings, counts) by the router.
- **Reality ≠ intent** — `/ai-context` documents only what is implemented; `.spec/` is invisible to it. The `.spec/` chain documents intent.
- **No Git writes** — the developer reviews with `git diff` and commits manually; `ralph.sh` does not stage, commit, reset, or edit Git exclusions.
- **No secrets** — `.env` is never read; env var names come from `.env.example` only.
- **Explicit, never blocking staleness** — sha256 stamps detect outdated inputs; the decision always belongs to the developer.

## License

[MIT](LICENSE)
