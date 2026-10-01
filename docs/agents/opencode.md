# OpenCode

Instale `skills/init`, `skills/plan`, `skills/task-builder` e
`skills/ai-context` no escopo escolhido com
`scripts/install-platform.sh --platform opencode`. O destino nativo é
`.opencode/skills/` no projeto e `~/.config/opencode/skills/` no usuário.
OpenCode também aceita os diretórios compatíveis `.agents/skills/` e
`.claude/skills/`, sem alterar o conteúdo canônico.

O executor é `scripts/ralph.sh --engine opencode`; eventos JSON são convertidos
em progresso provisório e o Gate 3 continua sendo o veredito final.
