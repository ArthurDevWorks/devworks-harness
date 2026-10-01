# Codex

O adaptador do Codex instala Skills de projeto em `.agents/skills/` e Skills de
usuário em `~/.codex/skills/`. Instale `skills/init`, `skills/plan`,
`skills/task-builder` e `skills/ai-context` com
`scripts/install-platform.sh --platform codex`.

O pacote também declara `skills/` no manifesto. O executor é
`scripts/ralph.sh --engine codex`; seu adaptador fica em
`scripts/engines/codex.sh` e mantém o Gate 3 em sandbox somente leitura.
