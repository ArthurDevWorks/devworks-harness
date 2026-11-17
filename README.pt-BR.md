# DEVWORKS Harness

Executa fases planejadas com Codex, Claude Code, OpenCode ou Antigravity. O Harness mantém especificação, estado, logs e verificação no projeto; não cria commits.

## Instalação

```sh
scripts/install-platform.sh --platform all --scope project --root /caminho/do/projeto
```

`all` instala os Skills de todas as CLIs disponíveis. Nenhuma plataforma fica
registrada como padrão do projeto.

## Uso

Crie e revise o plano com `plan`, detalhe uma fase com `task-builder` e execute no projeto alvo:

```sh
scripts/harness.sh configure
scripts/harness.sh run .spec/features/exemplo/phases/01-recurso/PHASES.md
```

Quando uma IA atingir o limite, escolha outra e retome:

```sh
scripts/harness.sh configure
scripts/harness.sh resume .spec/features/exemplo/phases/01-recurso/PHASES.md
```

As fases concluídas e as alterações não commitadas ficam preservadas. Revise o diff e faça o commit manualmente.

## Ralph Web

```sh
scripts/ralph-web.sh /caminho/do/projeto
```

Abra `http://127.0.0.1:7331` para escolher IA e modelos, salvar configuração, iniciar ou retomar um `PHASES.md`, acompanhar logs e encerrar a execução. O painel é local e aceita somente inputs dentro de `.spec/`.

## Configuração e desenvolvimento

`config/harness.json` guarda modelos e limites de sessão. Escolha a engine em
cada execução com `--engine`; flags e variáveis de ambiente continuam tendo
prioridade. Use `scripts/ralph.sh --help` para todas as opções.

```sh
scripts/test-ralph.sh
scripts/check-shell.sh
python3 -m unittest tests/test_dashboard.py
```

Consulte o [contrato de workflows](docs/agents/canonical-workflows.md) e o [guia Ralph com quatro engines](docs/guia-ralph-quatro-engines.md) quando precisar dos detalhes operacionais.
