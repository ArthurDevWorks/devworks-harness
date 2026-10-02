# Workflows canônicos

Os workflows do DEVWORKS Harness são `init`, `plan`, `task-builder` e
`ai-context`. A fonte canônica é `skills/<nome>/SKILL.md`; adaptadores de
plataforma somente escolhem o local de descoberta e não duplicam a lógica.

| Workflow | Entrada | Saída contratada |
|---|---|---|
| `init` | contexto e decisões do projeto | `.spec/init/*` |
| `plan` | uma necessidade ou especificação | `.spec/features/<slug>/SPEC.md` e `PLAN.md` |
| `task-builder` | uma fase aprovada do plano | `.spec/features/<slug>/phases/<NN>-<nome>/PHASES.md` |
| `ai-context` | código e configuração existentes | `AGENTS.md`, `CLAUDE.md`, `docs/agents/*` |

`PLAN.md` define as releases; `task-builder` detalha cada uma em seu
`PHASES.md`, usando `## Phase N: <título>`. Um arquivo executa uma fase; o
diretório `.spec/features/<slug>` executa todos os `phases/*/PHASES.md` em
ordem no mesmo run. O Ralph é a autoridade para execução, gates e estado;
nenhum workflow de contexto ou planejamento implementa código.

## Instalação

O instalador valida a presença e a versão publicada pela CLI escolhida. A
autenticação permanece uma exigência da própria CLI, sem armazenar tokens no
repositório. Ele confere os quatro Skills antes de criar qualquer cópia. No
escopo `project`, também instala o runtime em `scripts/`, o dashboard, os
adaptadores e a política de modelos, registrando a plataforma como engine
padrão do projeto.

```bash
scripts/install-platform.sh --platform codex --scope project
scripts/install-platform.sh --platform opencode --scope project
scripts/install-platform.sh --platform antigravity --scope project
scripts/install-platform.sh --platform claude --scope project
```

Para Claude Code, o plugin e os comandos existentes continuam suportados. Rode
`scripts/check-skill-drift.sh` antes de distribuir uma nova versão do harness.
