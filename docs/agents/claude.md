# Claude Code

O adaptador do Claude Code instala Skills de projeto em `.claude/skills/` e Skills
de usuário em `~/.claude/skills/`. Instale `skills/init`, `skills/plan`,
`skills/task-builder` e `skills/ai-context` com
`scripts/install-platform.sh --platform claude`.

O executor é `scripts/ralph.sh --engine claude`; seu adaptador fica em
`scripts/engines/claude.sh` e mantém o Gate 3 em sandbox somente leitura (`Read,Glob,Grep`).
