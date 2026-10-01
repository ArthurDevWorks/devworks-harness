# Antigravity

Instale `skills/init`, `skills/plan`, `skills/task-builder` e
`skills/ai-context` com `scripts/install-platform.sh --platform antigravity`.
Os Skills de projeto ficam em `.agents/skills/`; no escopo de usuário, o
instalador usa `~/.gemini/config/skills/`. Não existe uma cópia específica do
workflow.

O executor é `scripts/ralph.sh --engine antigravity`; toda a sintaxe da CLI
fica concentrada em `scripts/engines/antigravity.sh`.
