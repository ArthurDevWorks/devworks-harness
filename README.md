# DEVWORKS Harness

Run a planned phase with Codex, Claude Code, OpenCode, or Antigravity. The Harness keeps the specification, execution state, logs, and verification in the project; it never commits changes.

## Install

```sh
scripts/install-platform.sh --platform all --scope project --root /path/to/project
```

`all` installs the Skills for every available CLI. No platform is registered as
the project's default.

## Use

Create a plan with `plan`, review it, then create a selected phase with `task-builder`.

```sh
scripts/harness.sh configure
scripts/harness.sh run .spec/features/example/phases/01-feature/PHASES.md
```

When an engine reaches its limit, select another engine and resume:

```sh
scripts/harness.sh configure
scripts/harness.sh resume .spec/features/example/phases/01-feature/PHASES.md
```

Ralph preserves completed phases and uncommitted work. Review the diff and commit it yourself.

## Ralph Web

```sh
scripts/ralph-web.sh /path/to/project
```

Open `http://127.0.0.1:7331` to select the engine and models, save project settings, start or resume a `PHASES.md`, follow logs, and stop the active run. The panel is local and accepts only phase inputs below `.spec/`.

## Configuration and development

`config/harness.json` stores shared models and session limits. Select the engine
for each run with `--engine`; CLI flags and environment variables override saved
defaults. `scripts/ralph.sh --help` lists execution options.

```sh
scripts/test-ralph.sh
scripts/check-shell.sh
python3 -m unittest tests/test_dashboard.py
```

See [the workflow contract](docs/agents/canonical-workflows.md) and [the four-engine Ralph guide](docs/guia-ralph-quatro-engines.md) for operational details.
