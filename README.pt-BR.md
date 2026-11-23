# DEVWORKS Harness

Executa fases planejadas com Codex, Claude Code, OpenCode ou Antigravity. O Harness mantém especificação, estado, logs e verificação no projeto; não cria commits.

## Instalação

```sh
scripts/install-platform.sh --platform all --scope project --root /caminho/do/projeto
```

`all` (ou lista separada por vírgula, como `--platform codex,antigravity`) instala os Skills das CLIs selecionadas e registra as engines habilitadas em `config/harness.json`.

## Uso

Crie e revise o plano com `plan`, detalhe uma fase com `task-builder` e execute no projeto alvo:

```sh
scripts/ralph.sh                          # abre o painel Ralph Web por padrão
scripts/ralph.sh --headless --engine codex .spec/features/exemplo/phases/01-recurso/PHASES.md
scripts/ralph.sh --model-queue antigravity:gemini-4-argon-high,codex:gpt-6.2-sol --phases 1,2
```

Também é possível configurar e rodar pelo terminal com `scripts/harness.sh`:

```sh
scripts/harness.sh configure
scripts/harness.sh run .spec/features/exemplo/phases/01-recurso/PHASES.md
```

Quando uma IA atingir o limite, o Ralph avança automaticamente para o próximo item de `--model-queue` (ou `priority_queue` em `config/harness.json`), inclusive trocando de engine sem consumir ciclo de correção. Para retomar manualmente:

```sh
scripts/harness.sh resume .spec/features/exemplo/phases/01-recurso/PHASES.md
```

As fases concluídas e as alterações não commitadas ficam preservadas. Revise o diff e faça o commit manualmente.

## Ralph Web

```sh
scripts/ralph.sh                          # ou scripts/ralph-web.sh /caminho/do/projeto
```

Abra `http://127.0.0.1:7331` para habilitar engines, montar a fila de prioridade de modelos (`priority_queue` e `verify_queue`), selecionar fases específicas, salvar configuração, acompanhar logs e encerrar a execução. O painel é local e aceita somente inputs dentro de `.spec/`.

## Configuração e desenvolvimento

`config/harness.json` guarda `engines`, filas de prioridade (`priority_queue` / `verify_queue`), modelos e limites de sessão. Flags CLI (`--engine`, `--model-queue`, `--verify-queue`, `--phases`, `--headless`) e variáveis de ambiente continuam tendo prioridade. Use `scripts/ralph.sh --help` para todas as opções.

```sh
scripts/test-ralph.sh
scripts/check-shell.sh
python3 -m unittest tests/test_dashboard.py
```

Consulte o [contrato de workflows](docs/agents/canonical-workflows.md), o [guia completo do harness](docs/guia-completo-devworks-harness.md) e o [guia Ralph com quatro engines](docs/guia-ralph-quatro-engines.md) quando precisar dos detalhes operacionais.
