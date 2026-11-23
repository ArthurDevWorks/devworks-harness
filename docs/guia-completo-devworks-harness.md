# Guia Completo do DEVWORKS Harness

O DEVWORKS Harness é a plataforma de orquestração de desenvolvimento assistido
por agentes de IA. Ele combina especificação estruturada, decomposição de fases,
execução autônoma multi-engine com gates mecânicos e checkpoints humanos seguros
no Git.

---

## 1. Visão Geral e Ciclo do Harness

O fluxo operacional do harness segue um ciclo rigoroso de cinco etapas:

```text
[ai-context] (legado) ou [init] (novo)
         │
         ▼
       [plan] ────────► Gera SPEC.md e PLAN.md (visão macro/releases)
         │
         ▼
   [task-builder] ────► Detalha cada fase em PHASES.md executável
         │
         ▼
      [ralph] ────────► Execução autônoma com 4 gates e failover de modelos
         │
         ▼
  [revisão humana] ───► git diff, testes manuais e commit manual
```

### O que cada etapa entrega

| Componente | Papel principal | Artefatos gerados |
|---|---|---|
| **ai-context** | Documenta o código e contexto reais já existentes (sem usar `.spec/` como fonte). | `AGENTS.md`, `CLAUDE.md`, `docs/agents/*` |
| **init** | Especifica um projeto novo a partir de requisitos e decisões de arquitetura. | `.spec/init/*` |
| **plan** | Transforma o PRD ou demanda em fases maiores (releases), requisitos e critérios de aceite. | `.spec/features/<slug>/SPEC.md` e `PLAN.md` |
| **task-builder** | Detalha uma fase aprovada do plano em tarefas ordenadas, pequenas e verificáveis. | `.spec/features/<slug>/phases/<NN>-<nome>/PHASES.md` |
| **Ralph** | Executa as fases de forma autônoma, validando cada uma em quatro gates mecânicos. | Código alterado, histórico de runs e logs |
| **Desenvolvedor** | Revisa o diff acumulado, executa validações manuais e faz o commit no Git. | Checkpoint estável entre fases |

> **Invariante central:** O Ralph nunca executa `git commit`, `git add` ou `git reset`. Todo commit é manual e representa uma decisão humana.

---

## 2. Pré-requisitos e Segurança

- **Git:** Repositório inicializado em branch de trabalho dedicada.
- **Bash 4+:** Necessário para arrays associativos usados na suíte de testes do harness.
- **Python 3:** Necessário para o servidor do Ralph Web (`http://127.0.0.1:7331`).
- **Pelo menos uma CLI de engine instalada e autenticada:**
  - Codex (`codex`)
  - Claude Code (`claude`)
  - OpenCode (`opencode`)
  - Antigravity (`agy`)
- **Segredos e tokens:** Nunca armazene senhas, tokens ou chaves em arquivos de fase ou no repositório. As CLIs utilizam seus próprios mecanismos oficiais de autenticação no sistema.

---

## 3. Instalação e Atualização

### 3.1 Instalar no Projeto-Alvo

A partir de um clone central do DEVWORKS Harness:

```bash
# Instala os 4 Skills e o runtime para todas as CLIs instaladas:
scripts/install-platform.sh --platform all --scope project --root /caminho/do/projeto

# Ou para engines selecionadas (separadas por vírgula):
scripts/install-platform.sh --platform codex,antigravity --scope project --root /caminho/do/projeto
```

O instalador copia:
- **Skills canônicos:** `init`, `plan`, `task-builder` e `ai-context` para os diretórios esperados por cada engine (`.agents/skills/`, `.claude/skills/`, `.opencode/skills/`).
- **Runtime e scripts:** `scripts/ralph.sh`, `scripts/ralph-web.sh`, `scripts/ralph-watch.sh`, `scripts/harness.sh`, adaptadores `scripts/engines/` e dashboard web `scripts/dashboard/`.
- **Configuração:** `config/harness.json`, `config/model-policy.tsv` e `config/coding-style-profile.md`.

### 3.2 Atualizar uma Instalação Existente

Para atualizar os scripts e Skills em um projeto sem sobrescrever artefatos de trabalho (`.spec/`, `PHASES.md`, `.phases/`):

```bash
scripts/update-platform.sh --root /caminho/do/projeto
```

---

## 4. Workflows e Skills Canônicos

### 4.1 `ai-context` (Para projetos legados ou existentes)
Analisa o código real implementado e cria documentação de contexto em `AGENTS.md` e `docs/agents/`. Não altera código nem implementa features.

```text
Use o Skill ai-context. Analise o código que já existe e gere a documentação de contexto do projeto. Não implemente mudanças.
```

### 4.2 `init` (Para projetos novos)
Estabelece a base de arquitetura, decisões técnicas e descrição de escopo inicial do projeto em `.spec/init/`.

### 4.3 `plan` (Planejamento de entregas)
Lê o PRD ou necessidade e cria a especificação funcional (`SPEC.md`) e a visão de arquitetura e releases (`PLAN.md`) em `.spec/features/<slug>/`.

```text
Use o Skill plan para planejar a feature: descreva objetivo, regras de negócio e critérios de aceite. Leia AGENTS.md. Não implemente código.
```

### 4.4 `task-builder` (Detalhamento executável de fases)
Pega uma fase aprovada em `PLAN.md` e cria um `PHASES.md` auto-contido com tarefas pequenas, arquivos prováveis, comandos de teste e critérios binários de conclusão.

```text
Use o Skill task-builder para detalhar as fases aprovadas em .spec/features/<slug>/PLAN.md. Gere um PHASES.md por fase, sem implementar.
```

---

## 5. Execução com Ralph

### 5.1 Launcher Padrão (Ralph Web)

Ao rodar sem argumentos de execução direta, o Ralph abre a interface interativa no navegador:

```bash
cd /caminho/do/projeto
./scripts/ralph.sh
```

Acesse **`http://127.0.0.1:7331`**. No painel web você pode:
1. **Configurar prioridade de modelos:** Adicionar engines e modelos em ordem preferencial para failover automático.
2. **Definir verificador (Gate 3):** Configurar fila ou modelo para a auditoria de código.
3. **Selecionar fases:** Filtrar fases pendentes, selecionar todas ou marcar fases específicas via checkboxes.
4. **Disparar o run:** Iniciar a execução e acompanhar o fluxo por fase e tarefa.
5. **Logs ao vivo:** Visualizar o output das sessões em tempo real com auto-scroll.
6. **Encerrar execução:** Interromper o run a qualquer momento com o botão **"Encerrar Ralph"** (`/api/stop`), preservando o estado e alterações locais com segurança.

### 5.2 Modo Headless (Terminal)

Para rodar diretamente no terminal sem abrir interface gráfica:

```bash
# Execução direta informando a feature completa
./scripts/ralph.sh --headless --engine codex .spec/features/minha-feature

# Fila de prioridade multi-engine e execução de fases específicas
./scripts/ralph.sh --model-queue antigravity:gemini-4-argon-high,codex:gpt-6.2-sol --phases 1,3 .spec/features/minha-feature

# Especificando comando de teste e tolerância a falhas
./scripts/ralph.sh --engine claude --test-cmd "npm test" --keep-going .spec/features/minha-feature
```

### 5.3 Menu CLI com `scripts/harness.sh`

Permite configurar opções de execução e salvar de forma persistente em `config/harness.json`:

```bash
# Assistente interativo de configuração
scripts/harness.sh configure

# Iniciar execução com base nas preferências salvas
scripts/harness.sh run .spec/features/minha-feature

# Retomar execução a partir da primeira fase pendente
scripts/harness.sh resume .spec/features/minha-feature
```

---

## 6. Fila de Prioridade Multi-Engine e Failover Automático

O Ralph oferece suporte nativo a filas cross-engine (`--model-queue` e `--verify-queue` na CLI ou `priority_queue` / `verify_queue` em `config/harness.json`):

```bash
./scripts/ralph.sh --model-queue antigravity:gemini-4-argon-high,codex:gpt-6.2-sol,claude:sonnet
```

### Comportamento em Limite de Cota (Rate Limit / 429)
Quando o provedor ou engine em uso esgota sua cota ou atinge limite de requisições:
1. O Ralph detecta a mensagem de limite no log da sessão.
2. **Não consome ciclo de correção da fase.**
3. Avança automaticamente para o próximo item da fila (trocando inclusive de engine se necessário).
4. Continua a execução da mesma fase com a nova engine/modelo.
5. Se todas as engines da fila estiverem esgotadas, aguarda o timestamp oficial de reset antes de tentar novamente.

---

## 7. Os Quatro Gates Mecânicos

Para que uma fase seja marcada como concluída e avance para a próxima, ela precisa passar por quatro gates sucessivos:

```text
[ Sessão da Fase ] ──► G0 ──► G1 ──► G2 ──► G3 ──► [ Fase Concluída ]
                         │      │      │      │
                         └──────┴──────┴──────┴──► [ Ciclo de Correção ]
```

1. **G0 — Término da CLI:** Confere se o processo concluiu com sucesso real. Para OpenCode, exige `step_finish` e ausência de eventos de erro; para Antigravity, exige `result.status: SUCCESS`; para Codex e Claude, checa o exit code do processo.
2. **G1 — Mutação de código:** Avalia se a sessão alterou arquivos na árvore. Funciona como sinal diagnóstico: uma fase já implementada anteriormente pode não gerar alterações e ainda assim ser aprovada pelos gates subsequentes.
3. **G2 — Suíte de testes:** O Ralph executa o comando de testes do projeto fora do contexto da sessão do agente. Detecta automaticamente Docker/Sail, Composer, NPM, Pytest ou utiliza o informado em `--test-cmd`.
4. **G3 — Auditoria independente por task:** Uma sessão separada, executada em modo estritamente **somente leitura** (sandbox restrito), inspeciona o código-fonte gerado e confere cada critério de aceite com `TASK <n>: DONE` ou `TASK <n>: INCOMPLETE`. O veredito do Gate 3 tem autoridade máxima sobre qualquer declaração do implementador.

Se qualquer gate reprovar, um ciclo de correção é aberto com uma nova sessão e o log exato da causa da falha.

---

## 8. Perfil Universal de Engenharia (`config/coding-style-profile.md`)

Injetado automaticamente em todas as sessões do Ralph para orientar as IAs quanto a:
- Legibilidade e clareza de código sobre brevidade excessiva.
- Consulta obrigatória à documentação oficial das versões de ferramentas detectadas no projeto.
- Respeito estrito aos padrões observados na base de código existente antes de propor novas convenções.

---

## 9. Observabilidade e Diagnóstico

### Monitoramento TUI no Terminal

```bash
# Executar o monitor em outro terminal:
./scripts/ralph-watch.sh /caminho/do/projeto

# Ou rodar o Ralph com painel embutido:
./scripts/ralph.sh --engine opencode --dashboard .spec/features/minha-feature
```

### Estrutura de Arquivos em `.phases/`

- `.phases/current`: Aponta para o `run-id` atualmente selecionado.
- `.phases/runs/<run-id>/logs/`: Logs de saída de cada ciclo de implementação e verificação.
- `.phases/runs/<run-id>/prompts/`: Prompts auto-contidos gerados para cada sessão.
- `.phases/runs/<run-id>/state/run.tsv`: Estado consolidado da execução, fases e gates.
- `.phases/runs/<run-id>/state/live.tsv`: Estado em tempo real das tasks da fase ativa.
- `.phases/progress/<hash>.progress`: Registro de fases concluídas por hash do documento de entrada.
- `.phases/.ralph.lock/`: Trava de processo para evitar execuções concorrentes acidentais.

---

## 10. Guia de Diagnóstico Rápido

| Problema | Possível causa | Ação recomendada |
|---|---|---|
| `CLI não encontrado` | Executável ausente do `PATH` | Instale e faça login na CLI. Para Antigravity, o comando no terminal é `agy`. |
| Falha no G0 com OpenCode | Sessão interrompida ou evento de erro | Consulte o log da fase em `.phases/runs/.../logs/` e verifique se há evento `type: error`. |
| Falha no G0 com Antigravity | Status não bem-sucedido | O log da sessão deve registrar `result.status: SUCCESS`. Erros de quota disparam failover se houver fila. |
| Testes passaram mas G3 reprovou | Requisitos ausentes no código | Inspecione `*.verify-*.log`. A auditoria verifica a entrega concreta dos itens do `PHASES.md`, não apenas a ausência de quebra de testes. |
| Quota excedida | Limite de requisições ou créditos | Configure `--model-queue` ou salve uma fila multi-engine em `config/harness.json`. |
| Execução travada | Processo bloqueado por rede ou dependência | No Ralph Web, clique em **Encerrar Ralph**. No terminal, envie `SIGINT` (`Ctrl+C`). |

---

## 11. Validação do Próprio Harness

Para desenvolvedores e mantenedores do harness:

```bash
scripts/test-ralph.sh                        # Suíte de testes funcionais (281 asserts)
scripts/check-shell.sh                       # Validação sintática bash
scripts/check-init-drift.sh                  # Alinhamento de redação entre prompts
scripts/check-skill-drift.sh                 # Sincronia entre Skills e adaptadores
python3 -m unittest tests/test_dashboard.py  # Testes unitários do dashboard web
git diff --check                             # Checagem de formatação e whitespace
```
