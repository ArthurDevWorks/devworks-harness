# Guia prático do Ralph: Codex, Claude, OpenCode e Antigravity

O Ralph é o orquestrador autônomo do DEVWORKS Harness. Ele executa um documento
de fases (`PHASES.md`) ou um diretório de feature completo (`.spec/features/<slug>`)
de ponta a ponta sem intervenção humana. Cada fase — inclusive cada ciclo de
correção — abre uma sessão nova do engine selecionado, valida o resultado em
quatro gates mecânicos e preserva as alterações na árvore Git para revisão e commit
manual pelo desenvolvedor.

Por padrão, executar `./scripts/ralph.sh` sem argumentos de execução direta abre o
painel interativo **Ralph Web** (`http://127.0.0.1:7331`) no navegador para
selecionar engines, montar filas de prioridade cross-engine, filtrar fases e
acompanhar ou interromper o run. O Ralph também pode ser executado diretamente pelo
terminal em modo headless ou pelo menu CLI `scripts/harness.sh`.

Use-o sempre em uma branch descartável ou em um clone de trabalho. As sessões de
implementação podem editar arquivos e executar comandos sem intervenção.

## 1. Antes de começar e instalação

Você precisa estar na raiz de um repositório Git. A árvore pode conter mudanças
staged, unstaged ou não rastreadas: Ralph não as bloqueia nem altera o índice.

### 1.1 Instalação das CLIs

Instale e autentique os engines que pretende utilizar:

| Engine | Executável | Instalação/autenticação |
|---|---|---|
| Codex | `codex` | `npm install -g @openai/codex` |
| Claude Code | `claude` | `npm install -g @anthropic-ai/claude-code` |
| OpenCode | `opencode` | [documentação do OpenCode](https://opencode.ai/docs) |
| Antigravity | `agy` | [instalação do Antigravity](https://antigravity.google/docs/cli/install/) |

### 1.2 Instalação do Harness no projeto-alvo

A partir de um checkout central do DEVWORKS Harness, instale os Skills canônicos
(`init`, `plan`, `task-builder` e `ai-context`) e o runtime no projeto-alvo:

```bash
# Instala suporte a todas as engines instaladas
scripts/install-platform.sh --platform all --scope project --root /caminho/do/projeto

# Ou selecione uma lista específica de engines
scripts/install-platform.sh --platform codex,antigravity --scope project --root /caminho/do/projeto
```

O instalador copia os Skills para o local nativo de cada engine (`.agents/skills/`,
`.claude/skills/`, `.opencode/skills/`), copia os scripts de execução
(`scripts/ralph.sh`, `scripts/ralph-web.sh`, `scripts/ralph-watch.sh`,
`scripts/harness.sh`), o dashboard web, os adaptadores e a política de modelos,
além de registrar as engines habilitadas em `config/harness.json`.

Para atualizar uma instalação já existente em um projeto sem sobrescrever seus
artefatos de trabalho:

```bash
scripts/update-platform.sh --root /caminho/do/projeto
```

### 1.3 Perfil universal de engenharia e estilo

O arquivo `config/coding-style-profile.md` distribui preferências universais de
legibilidade, documentação oficial e padrões de código para todos os prompts do
Ralph, mantendo agnosticismo de stack enquanto reforça boas práticas.

### 1.4 Entradas aceitas

O Ralph aceita os seguintes inputs:

1. **Diretório de feature (recomendado para entregas completas):**
   ```bash
   ./scripts/ralph.sh .spec/features/minha-feature
   ```
   Executa todos os arquivos `phases/*/PHASES.md` em ordem sequencial no mesmo run.

2. **Arquivo de fase específico:**
   ```bash
   ./scripts/ralph.sh .spec/features/minha-feature/phases/01-recurso/PHASES.md
   ```

3. **Input padrão (sem argumentos posicionais):**
   Resolve automaticamente para `.spec/init/project-phases.md` (ou
   `.spec/project-phases.md` em repositórios pré-init).

O documento deve usar headings no formato `## Phase N: Título` e tarefas em
itens `- [ ]`. Sub-fases podem ser estruturadas em `### Phase N.M:`.

## 2. Escolhendo, configurando e iniciando um engine

### 2.1 Interface gráfica (Ralph Web — padrão)

Executar o Ralph sem flags headless inicia o servidor local e abre o navegador:

```bash
./scripts/ralph.sh
# ou explicitamente:
./scripts/ralph-web.sh .
```

No painel (`http://127.0.0.1:7331`), você pode:
- Visualizar as engines ativas e adicionar modelos à fila de prioridade;
- Definir o verificador do Gate 3 (seguir a fila de implementação ou modelo fixo);
- Escolher o documento `.spec/` e marcar apenas fases específicas (Pendentes, Todas, Nenhuma ou seleção granular);
- Ajustar limites de tempo e salvar a configuração em `config/harness.json`;
- Iniciar a execução e acompanhar logs em tempo real;
- Encerrar a execução em andamento com o botão **"Encerrar Ralph"**.

### 2.2 Modo Headless (Terminal)

Para rodar diretamente no terminal sem abrir o navegador:

```bash
# Execução direta com engine individual
./scripts/ralph.sh --headless --engine codex .spec/features/minha-feature/PHASES.md

# Fila de prioridade multi-engine com seleção de fases
./scripts/ralph.sh --model-queue antigravity:gemini-4-argon-high,codex:gpt-6.2-sol --phases 1,3

# Claude Code
./scripts/ralph.sh --engine claude .spec/features/minha-feature

# OpenCode
./scripts/ralph.sh --engine opencode .spec/features/minha-feature

# Antigravity com timeout customizado
RALPH_ANTIGRAVITY_TIMEOUT=45m ./scripts/ralph.sh --engine antigravity .spec/features/minha-feature
```

### 2.3 Fila de prioridade cross-engine e failover automático

Ralph suporta **fila de prioridade multi-engine** (`--model-queue` e
`--verify-queue` na CLI, ou `priority_queue` e `verify_queue` em
`config/harness.json` / Ralph Web).

Quando uma IA atinge seu limite de cota ou taxa (rate limit / 429), o Ralph
**avança automaticamente para o próximo modelo/engine da fila**, sem consumir
ciclo de correção e sem perder as alterações já acumuladas na fase atual.

```bash
./scripts/ralph.sh --model-queue antigravity:gemini-4-argon-high,codex:gpt-6.2-sol,claude:sonnet
```

### 2.4 Menu CLI de configuração e retomada (`scripts/harness.sh`)

O script `scripts/harness.sh` oferece uma interface de terminal simplificada que
armazena e lê suas opções de `config/harness.json`:

```bash
# Configura interativamente a fila de prioridade, modelos e limites
scripts/harness.sh configure

# Inicia a execução headless com base na configuração salva
scripts/harness.sh run .spec/features/minha-feature

# Retoma a execução a partir da primeira fase pendente
scripts/harness.sh resume .spec/features/minha-feature
```

### 2.5 Contrato de execução por engine

| Engine | Implementador | Verificador do Gate 3 |
|---|---|---|
| Codex | `codex exec --sandbox danger-full-access` | sandbox `read-only` |
| Claude | `claude --dangerously-skip-permissions` | somente `Read,Glob,Grep` |
| OpenCode | `opencode run --auto --format json` | configuração inline: apenas `read`, `glob`, `grep` |
| Antigravity | `agy -p ... --mode accept-edits --dangerously-skip-permissions` | `--mode plan --sandbox`, sem a flag perigosa |

OpenCode recebe o prompt pelo `stdin` e publica eventos JSON. Antigravity usa
`agy` em modo headless com `--output-format stream-json`. Cada sessão possui
timeout configurável (`RALPH_IMPLEMENTATION_TIMEOUT` e `RALPH_VERIFICATION_TIMEOUT`).

### 2.6 Política de modelos por engine

A rota configurável em `config/model-policy.tsv` é aplicada automaticamente pelo
Antigravity (`agy`):

| Papel/perfil Antigravity | Primário | Fallbacks |
|---|---|---|
| Plan e Task Builder | Gemini 4 Argon High | Claude Opus 5.5 High → Gemini 3.8 Flash High |
| `routine` | Gemini 3.8 Flash Medium | Flash High → Gemini 4 Argon Medium |
| `standard` | Gemini 4 Argon Medium | Flash High → Claude Opus 5.5 High |
| `complex` | Gemini 4 Argon High | Claude Opus 5.5 High → Flash High |
| Verificação | Claude Sonnet 5.5 High | Gemini 3.8 Flash High |

Para as demais CLIs, modelos recomendados por faixa de trabalho:

| Engine | Rotina | Padrão | Planejamento/tarefa difícil |
|---|---|---|---|
| Codex | `gpt-6-luna` | `gpt-6.1-sol` | `gpt-6.1-sol` com maior raciocínio |
| Claude Code | `haiku` | `sonnet` | `opus` ou `fable` para trabalho complexo |
| OpenCode | Flash/Luna rápido | Sonnet ou GPT-6.1 Sol | Opus ou Fable |

No OpenCode, consulte os IDs com `opencode models`; no Claude Code, use os
aliases oficiais (`sonnet`, `opus`, `haiku`).

## 3. O que o Ralph garante (Os quatro gates)

Cada fase passa obrigatoriamente pelos quatro gates mecânicos abaixo. Se qualquer
gate falhar, um ciclo de correção é aberto com uma **nova** sessão informando a
causa real da falha:

| Gate | Verificação |
|---|---|
| G0 | **Término mecânico:** A CLI realmente concluiu com sucesso? OpenCode exige `step_finish` e ausência de eventos de erro; Antigravity exige `result.status: SUCCESS`; Codex e Claude validam o código de saída do processo. |
| G1 | **Mutação de código:** A sessão alterou a árvore Git? É um sinal, não veredito: uma fase já implementada pode não alterar arquivos e ainda assim ser aprovada. |
| G2 | **Suíte de testes:** O comando de teste do projeto passa quando executado pelo Ralph (fora da sessão do agente)? Detecta automaticamente ambientes comuns (como Laravel Sail, composer test, npm test) ou usa `--test-cmd`. |
| G3 | **Auditoria independente:** Um verificador separado (em sandbox somente leitura) inspeciona o código e avalia cada tarefa com `TASK <n>: DONE` ou `TASK <n>: INCOMPLETE`. Esse veredito tem precedência sobre o que o implementador declarou. Validações manuais sem automação não devem ter checkbox no PHASES.md. |

Quando todos os gates estão verdes, a fase é concluída e as alterações acumuladas
permanecem na árvore. Revise o diff e faça o commit manualmente.

## 4. Acompanhar e controlar uma execução

### 4.1 Monitoramento via Ralph Web

Ao iniciar com `scripts/ralph.sh` ou `scripts/ralph-web.sh .`, abra
`http://127.0.0.1:7331` no navegador. O dashboard oferece:
- Visualização de todas as fases e tarefas em tempo real;
- Acompanhamento dos 4 gates mecânicos por fase;
- Painel de logs ao vivo com auto-scroll ("Seguindo" / "Ir ao fim");
- Botão **"Encerrar Ralph"** (`/api/stop`) para interromper o processo de forma limpa.

### 4.2 Monitoramento no Terminal (TUI)

```bash
# Painel TUI em outro terminal
./scripts/ralph-watch.sh .

# Painel TUI integrado no mesmo terminal
./scripts/ralph.sh --engine codex --dashboard .spec/features/minha-feature
```

Claude, OpenCode e Antigravity transmitem eventos em stream, permitindo o
rastreamento tarefa a tarefa através dos marcadores:

```text
RALPH-TASK 1 START
RALPH-TASK 1 DONE
```

Se o agente não emitir esses marcadores, o Ralph usa eventos de escrita de
arquivos como reserva de progresso provisório até a auditoria definitiva do Gate 3.

### 4.3 Arquivos de diagnóstico

```text
.phases/runs/<run-id>/logs/       # output de cada ciclo e verificador
.phases/runs/<run-id>/prompts/    # prompt auto-contido enviado a cada sessão
.phases/runs/<run-id>/state/      # estado consolidado (run.tsv) e progresso ao vivo (live.tsv)
.phases/progress/<hash>.progress  # fases já concluídas para o mesmo documento
```

## 5. Retomar, limitar e controlar escopo

```bash
# Executa apenas fases específicas (ex: apenas as fases 1 e 3)
./scripts/ralph.sh --phases 1,3 .spec/features/minha-feature

# Reexecutar a partir da fase 3 (limpa do progresso as fases posteriores)
./scripts/ralph.sh --from 3 .spec/features/minha-feature

# Retomar execução respeitando fases já concluídas
./scripts/harness.sh resume .spec/features/minha-feature

# Continuar execução mesmo se uma fase falhar (trabalho parcial fica na árvore)
./scripts/ralph.sh --keep-going .spec/features/minha-feature

# Definir limite máximo de ciclos de correção por fase (padrão: 3)
./scripts/ralph.sh --max-cycles 2 .spec/features/minha-feature

# Definir explicitamente o comando de testes do projeto (Gate 2)
./scripts/ralph.sh --test-cmd 'vendor/bin/sail test' .spec/features/minha-feature

# Desligar o Gate 3 conscientemente quando necessário
./scripts/ralph.sh --no-verify .spec/features/minha-feature
```

Se uma engine atingir o limite de requisições ou cota, o Ralph não consome ciclo
de correção: ele ativa o próximo item da fila de prioridade (`--model-queue`), ou
aguarda o timestamp de reset antes de tentar novamente.

## 6. Diagnóstico rápido

| Sintoma | Causa provável | Ação recomendada |
|---|---|---|
| `CLI não encontrado` | Executável ausente no `PATH` | Instale e autentique a CLI correspondente. Para Antigravity, o executável é `agy`. |
| Árvore suja no início | Mudanças prévias no repositório | Não bloqueia a execução. Ralph preserva o índice e o working tree. Revise o diff ao término. |
| OpenCode falha no G0 | Erro de execução da CLI | Verifique o log: deve conter `step_finish` e nenhum evento `type: error`. |
| Antigravity falha no G0 | Sessão não concluída com sucesso | Verifique o log: o último evento `result` deve ter `status: SUCCESS`. |
| Limite de taxa/cota atingido | Quota esgotada na engine atual | Configure uma fila multi-engine com `--model-queue` ou `scripts/harness.sh configure` para failover automático. |
| Painel não avança por task | Falta de marcadores textuais | Verifique `live.tsv`: se o agente não publicar `RALPH-TASK`, o progresso provisório dependerá de escrita em arquivos até o Gate 3. |
| Gate 3 reprova com testes verdes | Tarefas incompletas na prática | Leia o log `*.verify-*.log`. Os testes podem passar sem que todos os requisitos da fase tenham sido entregues. |
| Processo travado ou indesejado | Necessidade de cancelamento | No Ralph Web, clique em **Encerrar Ralph**. No terminal, envie `Ctrl+C`. |

## 7. Validar alterações no próprio harness

Antes de distribuir ou commitar alterações no DEVWORKS Harness, execute a suíte
completa de testes e validação sintática:

```bash
scripts/test-ralph.sh
scripts/check-shell.sh
scripts/check-init-drift.sh
scripts/check-skill-drift.sh
python3 -m unittest tests/test_dashboard.py
git diff --check
```

`scripts/test-ralph.sh` executa mais de 280 asserções cobrindo gates, failover
cross-engine, controle de fases e compatibilidade entre plataformas. Requer
Bash 4+.

## Checklist de uma execução segura

- [ ] Repositório alvo e branch de trabalho verificados.
- [ ] As CLIs pretendidas estão instaladas e autenticadas.
- [ ] O harness foi instalado ou atualizado no projeto (`install-platform.sh` / `update-platform.sh`).
- [ ] O comando de testes foi detectado ou especificado com `--test-cmd`.
- [ ] Fila de prioridade de modelos configurada para evitar bloqueios por rate limit.
- [ ] Logs e status dos 4 gates revisados após a conclusão de cada fase.
- [ ] `git diff` inspecionado manualmente antes de realizar o commit final.
