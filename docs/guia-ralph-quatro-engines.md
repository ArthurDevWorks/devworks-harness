# Guia prático do Ralph: Codex, Claude, OpenCode e Antigravity

O Ralph executa um documento de fases (`PHASES.md`) de maneira autônoma. Cada
fase — inclusive cada ciclo de correção — abre uma sessão nova do engine
selecionado, valida o resultado em quatro gates e deixa as alterações na árvore
para revisão e commit manual quando a fase está verde.

Use-o em uma branch descartável ou em um clone de trabalho. As sessões de
implementação podem editar arquivos e executar comandos sem intervenção.

## 1. Antes de começar

Você precisa estar na raiz de um repositório Git. A árvore pode conter mudanças
staged, unstaged ou não rastreadas: Ralph não as bloqueia nem altera o índice.

Instale e autentique apenas o engine que pretende usar:

| Engine | Executável | Instalação/autenticação |
|---|---|---|
| Codex | `codex` | `npm install -g @openai/codex` |
| Claude Code | `claude` | `npm install -g @anthropic-ai/claude-code` |
| OpenCode | `opencode` | [documentação do OpenCode](https://opencode.ai/docs) |
| Antigravity | `agy` | [instalação do Antigravity](https://antigravity.google/docs/cli/install/) |

O input padrão é `.spec/init/project-phases.md`. Também é possível apontar um
arquivo de feature diretamente:

```bash
./scripts/ralph.sh .spec/features/minha-feature/PHASES.md
```

O documento deve usar headings no formato `## Phase N: Título` e tarefas em
itens `- [ ]`. Não altere o formato das fases apenas para trocar de engine.

## 2. Escolhendo e iniciando um engine

```bash
# Codex (padrão)
./scripts/ralph.sh --engine codex

# Claude Code
./scripts/ralph.sh --engine claude

# OpenCode
./scripts/ralph.sh --engine opencode

# Antigravity
./scripts/ralph.sh --engine antigravity
```

| Engine | Implementador | Verificador do Gate 3 |
|---|---|---|
| Codex | `codex exec --sandbox danger-full-access` | sandbox `read-only` |
| Claude | `claude --dangerously-skip-permissions` | somente `Read,Glob,Grep` |
| OpenCode | `opencode run --auto --format json` | configuração inline: apenas `read`, `glob`, `grep` |
| Antigravity | `agy -p ... --mode accept-edits --dangerously-skip-permissions` | `--mode plan --sandbox`, sem a flag perigosa |

OpenCode recebe o prompt pelo `stdin` e publica eventos JSON. Antigravity usa
`agy` em modo headless com `--output-format stream-json`; por padrão, cada
sessão pode durar até 30 minutos. Ajuste quando uma fase exigir mais tempo:

```bash
RALPH_ANTIGRAVITY_TIMEOUT=45m \
  ./scripts/ralph.sh --engine antigravity .spec/features/minha-feature/PHASES.md
```

`RALPH_VERIFY_MODEL` é opcional e é repassada ao verificador, sem mudar o
modelo do implementador:

```bash
RALPH_VERIFY_MODEL=meu-modelo \
  ./scripts/ralph.sh --engine opencode
```

## 3. O que o Ralph garante

Cada fase passa pelos quatro gates abaixo. Um gate vermelho cria um ciclo de
correção com uma **nova** sessão e a causa real da falha.

| Gate | Verificação |
|---|---|
| G0 | A CLI realmente concluiu: OpenCode exige `step_finish` e ausência de evento de erro; Antigravity exige `result.status: SUCCESS`; Codex e Claude mantêm seus contratos anteriores. |
| G1 | A sessão alterou a árvore? É sinal, não veredito: fase já implementada pode não alterar arquivos. |
| G2 | O comando de teste do projeto passa, executado pelo Ralph fora da sessão do agente. |
| G3 | Um verificador independente responde `TASK <n>: DONE/INCOMPLETE` a partir do código real. Esse veredito prevalece sobre a impressão do implementador. Validações manuais sem ambiente seguro devem ser documentadas sem checkbox, fora das tasks executáveis. |

Quando todos os gates passam, Ralph marca a fase como concluída e preserva as
alterações acumuladas na árvore. Revise o diff e faça o commit manualmente.

## 4. Acompanhar uma execução

O estado é gravado sempre em `.phases/runs/<run-id>/state/`; `.phases/current`
aponta para o run selecionado e o TUI mantém compatibilidade com o layout plano:

```bash
# Painel em outro terminal
./scripts/ralph-watch.sh .

# Painel no mesmo terminal
./scripts/ralph.sh --engine opencode --dashboard
```

Claude, OpenCode e Antigravity atualizam tarefas durante a execução. O prompt
pede os marcadores textuais abaixo, que são a fonte primária do painel:

```text
RALPH-TASK 1 START
RALPH-TASK 1 DONE
```

Se o agente não os publicar, Ralph usa eventos de ferramentas de escrita como
reserva. No encerramento, o Gate 3 substitui esse progresso provisório pelo
veredito verificado. Codex não expõe stream equivalente, por isso seu painel é
granular por fase até o Gate 3.

Arquivos úteis de diagnóstico:

```text
.phases/runs/<run-id>/logs/       # output de cada ciclo e verificador
.phases/runs/<run-id>/prompts/    # prompt auto-contido enviado em cada sessão
.phases/runs/<run-id>/state/      # estado consolidado e progresso ao vivo
.phases/progress/<input-hash>.progress # fases concluídas para o mesmo input
```

## 5. Retomar, limitar e controlar escopo

```bash
# Reexecutar a partir da fase 3; limpa o progresso das fases seguintes
./scripts/ralph.sh --from 3

# Continuar após uma falha; o trabalho parcial permanece na árvore
./scripts/ralph.sh --keep-going

# Limitar ciclos de correção por fase
./scripts/ralph.sh --max-cycles 2

# Definir explicitamente o comando de testes do projeto
./scripts/ralph.sh --test-cmd 'vendor/bin/sail test'

# Desligar o Gate 3 apenas quando isso for uma decisão consciente
./scripts/ralph.sh --no-verify
```

Por padrão, um limite de uso não consome ciclo de correção: Ralph lê apenas o
fim do log, aguarda o reset ou o fallback configurado e repete a mesma fase.
Os controles são `RALPH_MAX_LIMIT_WAITS`, `RALPH_LIMIT_WAIT_DEFAULT` e
`RALPH_LIMIT_BUFFER`.

## 6. Diagnóstico rápido

| Sintoma | Ação recomendada |
|---|---|
| `CLI não encontrado` | Instale o executável indicado pelo preflight e autentique a CLI. Para Antigravity, o binário esperado é `agy`. |
| Árvore suja no início | Não é bloqueio: Ralph preserva alterações staged, unstaged e não rastreadas. Revise o diff acumulado ao fim do run. |
| OpenCode para no G0 | Abra o log do ciclo. Deve existir `step_finish` e não pode existir um evento JSON `type: error`. |
| Antigravity para no G0 | Abra o log do ciclo. O último evento `result` deve ter `status: SUCCESS`. `ERROR`, `WAITING` ou ausência de resultado são falhas. |
| Painel não avança por tarefa | Verifique `live.tsv` e o log: os marcadores `RALPH-TASK` têm prioridade; sem eles, somente eventos de escrita que possam ser associados à tarefa dão a reserva de progresso. |
| Gate 3 reprova apesar de testes verdes | Leia o log `*.verify-*.log`; os testes não provaram que cada item da fase foi entregue. O ciclo seguinte recebe as tasks `INCOMPLETE` literalmente. |

## 7. Validar alterações no próprio harness

```bash
scripts/test-ralph.sh
scripts/check-shell.sh
scripts/check-init-drift.sh
scripts/check-skill-drift.sh
python3 -m unittest tests/test_dashboard.py
git diff --check
```

`scripts/test-ralph.sh` exige Bash 4+ porque usa arrays associativos. O Bash
3.2 fornecido pelo macOS ainda permite a validação sintática de
`scripts/check-shell.sh`, mas não executa a suíte funcional.

## Checklist de uma execução segura

- [ ] O repositório e o arquivo de fases corretos foram conferidos.
- [ ] A CLI selecionada está instalada e autenticada.
- [ ] O engine foi escolhido conscientemente para um ambiente confiável.
- [ ] O comando de testes foi detectado ou informado explicitamente.
- [ ] Logs e gates foram revisados antes de revisar o diff acumulado.
- [ ] As alterações foram revisadas e o commit manual foi feito quando desejado.
