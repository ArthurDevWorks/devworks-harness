# DEVWORKS Harness

Run a planned phase with Codex, Claude Code, OpenCode, or Antigravity. The Harness keeps the specification, execution state, logs, and verification in the project; it never commits changes.

## Install

```sh
scripts/install-platform.sh --platform all --scope project --root /path/to/project
```

`all` (or a comma-separated list such as `--platform codex,antigravity`) installs the Skills for the selected CLIs and records the enabled engines in `config/harness.json`.

## Use

Create a plan with `plan`, review it, then create a selected phase with `task-builder`.

```sh
scripts/ralph.sh                          # opens Ralph Web by default
scripts/ralph.sh --headless --engine codex .spec/features/example/phases/01-feature/PHASES.md
scripts/ralph.sh --model-queue antigravity:gemini-4-argon-high,codex:gpt-6.2-sol --phases 1,2
```

You can also configure and run from the terminal via `scripts/harness.sh`:

```sh
scripts/harness.sh configure
scripts/harness.sh run .spec/features/example/phases/01-feature/PHASES.md
```

When an engine hits its usage limit, Ralph automatically fails over to the next route in `--model-queue` (or `priority_queue` in `config/harness.json`), including across engines, without consuming a fix cycle. To resume manually:

```sh
scripts/harness.sh resume .spec/features/example/phases/01-feature/PHASES.md
```

Ralph preserves completed phases and uncommitted work. Review the diff and commit it yourself.

## Ralph Web

```sh
scripts/ralph.sh                          # or scripts/ralph-web.sh /path/to/project
```

Open `http://127.0.0.1:7331` to toggle engines, build the model priority queue (`priority_queue` and `verify_queue`), select specific phases, save project settings, follow logs, and stop the active run. The panel is local and accepts only phase inputs below `.spec/`.

## Configuration and development

`config/harness.json` stores `engines`, priority queues (`priority_queue` / `verify_queue`), models, and session limits. CLI flags (`--engine`, `--model-queue`, `--verify-queue`, `--phases`, `--headless`) and environment variables override saved defaults. `scripts/ralph.sh --help` lists execution options.

```sh
scripts/test-ralph.sh
scripts/check-shell.sh
python3 -m unittest tests/test_dashboard.py
```

See [the workflow contract](docs/agents/canonical-workflows.md) and [the four-engine Ralph guide](docs/guia-ralph-quatro-engines.md) for operational details.
