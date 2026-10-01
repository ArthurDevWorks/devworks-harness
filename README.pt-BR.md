# DEVWORKS Harness

Harness standalone para levar um projeto da ideia à implementação de forma
estruturada: especificação, planejamento em releases, tarefas executáveis e
execução com validação mecânica. Funciona com Codex, Claude Code, OpenCode e
Antigravity; o plugin Claude permanece apenas como adaptador de compatibilidade.

O harness é **agnóstico de stack**: quem define linguagem, framework, comandos e convenções são os documentos do próprio projeto (`AGENTS.md`, `CLAUDE.md`, cadeia `.spec/`), nunca o harness.

## Visão geral do fluxo

```
 IDEIA                                             CÓDIGO
   │                                                 ▲
   ▼                                                 │
 init ────────────────────────► .spec/init/          │
 (PRD, histórias, schema e      mapa de releases)    │
   │                                                 │
   │            plan ─► SPEC.md + PLAN.md             │
   │            task-builder ─► PHASES.md de 1 fase   │
   ▼                                                 │
PHASES.md de 1 fase ──────────────────────► scripts/ralph.sh
                                            (execução autônoma
                                             com 4 gates)

 /ai-context ─► AGENTS.md + docs/agents/*  (documenta o código JÁ implementado;
                                            alimenta /plan e o ralph)
```

Quatro workflows que se encaixam:

1. **`init`** — do PRD ao contexto inicial do projeto (descrição → histórias → schema sugerido → mapa de releases).
2. **`plan`** — de uma descrição de feature a SPEC formal + mapa de releases.
3. **`task-builder`** — detalha uma release aprovada em tarefas pequenas e gera o `PHASES.md` de uma única fase.
4. **`ralph.sh`** — executa qualquer documento de fases de forma autônoma, uma sessão nova de agente por fase, com gates mecânicos; as mudanças ficam para revisão e commit manual.

Transversal a tudo: **`/ai-context`** mantém a árvore de contexto (`AGENTS.md`, `CLAUDE.md`, `docs/agents/*.md`) sincronizada com o código real.

## Estado atual e fluxo recomendado

Os quatro Skills canônicos estão em `skills/` e são instaláveis nas quatro
engines. Todos produzem os mesmos artefatos; muda apenas a forma de chamar o
Skill em cada interface.

| Situação | Fluxo |
|---|---|
| Projeto novo | `init` com o PRD → `plan` → aprovar releases → `task-builder` da próxima fase → Ralph → validar e commitar |
| Projeto legado | `ai-context` → revisar documentação AS IS → `plan` da manutenção → `task-builder` → Ralph → validar regressões e commitar |

O `plan` define as fases grandes, semelhantes a releases. O `task-builder`
detalha apenas a fase escolhida e gera um `PHASES.md` próprio. Esta é a forma
recomendada de executar um ciclo por vez.

O Ralph também aceita um documento com várias fases: ele as executa **em
sequência**, uma sessão nova por fase. Por padrão, para na primeira falha;
`--keep-going` preserva o trabalho parcial e segue para a próxima. A opção
`--from N` começa na fase N e continua nas posteriores - ela não limita a
execução a uma única fase.

## Instalação

O DEVWORKS Harness é independente: mantenha este repositório em qualquer
diretório local e use seus scripts a partir do projeto-alvo. Não depende de
plugin, marketplace ou namespace de Claude Code.

Os Skills canônicos `init`, `plan`, `task-builder` e `ai-context` estão em
`skills/`. O instalador copia o mesmo conteúdo para o destino de descoberta de
cada engine; não grava tokens nem depende de dependências do projeto-alvo:

```bash
scripts/install-platform.sh --platform codex --scope project
scripts/install-platform.sh --platform claude --scope project
scripts/install-platform.sh --platform opencode --scope user
scripts/install-platform.sh --platform antigravity --scope project
```

Veja o [contrato de workflows multiplataforma](docs/agents/canonical-workflows.md).

O `ralph.sh` é um script bash independente — copie ou referencie `scripts/ralph.sh` e rode direto no repositório do projeto-alvo.

### Destinos de instalação

| Engine | Projeto | Usuário |
|---|---|---|
| Codex | `.agents/skills/` | `~/.codex/skills/` |
| Claude Code | `.claude/skills/` | `~/.claude/skills/` |
| OpenCode | `.opencode/skills/` | `~/.config/opencode/skills/` |
| Antigravity | `.agents/skills/` | `~/.gemini/config/skills/` |

Use `--check` para validar a CLI e o destino sem copiar arquivos. A instalação
normal exige CLI autenticada e valida os quatro Skills antes de escrever.

## Novidades: DEVWORKS, múltiplos agentes e observabilidade

O Harness agora tem um núcleo de execução independente de fornecedor. Os
workflows `init`, `plan`, `task-builder` e `ai-context` mantêm os mesmos
contratos de saída. O plugin Claude preserva os comandos legados, mas não é a
fonte canônica nem uma dependência das outras engines:

```text
.spec/init/*
.spec/features/<slug>/*
AGENTS.md, CLAUDE.md e docs/agents/*
PHASES.md executável pelo Ralph
```

O instalador abaixo é o ponto único de distribuição. `--check` valida a CLI e
o destino sem copiar arquivos; a instalação normal valida os quatro Skills
antes de criar qualquer diretório:

```bash
scripts/install-platform.sh --platform codex --scope project
scripts/install-platform.sh --platform claude --scope project
scripts/install-platform.sh --platform opencode --scope user
scripts/install-platform.sh --platform antigravity --scope project
```

`--check` verifica se a CLI escolhida está disponível e responde com sua
versão. A autenticação permanece sob responsabilidade da CLI e não é gravada
no repositório.

### Política inicial de modelos

`config/model-policy.tsv` centraliza a política da engine Antigravity. O Ralph
aplica automaticamente os perfis de execução e verificação; para `plan` e
`task-builder`, escolha a rota correspondente na interface da engine.

| Papel | Primário | Fallbacks |
|---|---|---|
| Plan e Task Builder | Claude Opus 4.6 Thinking | Gemini 3.1 Pro High → Gemini 3.8 Flash High |
| Execução `routine` | Gemini 3.8 Flash Medium | Flash High → Pro High |
| Execução `standard` | Gemini 3.8 Flash High | Pro High → Claude Opus |
| Execução `complex` | Gemini 3.1 Pro High | Claude Opus → Flash High |
| Verificação | Claude Sonnet 4.6 | Gemini 3.8 Flash High |

Em limite de uso na Antigravity, o Ralph troca para o próximo modelo da rota e
continua a mesma fase. Falha de teste ou gate vermelho abre um ciclo normal de
correção; não troca modelo automaticamente.

### Execução, histórico e lock

Cada execução recebe o ID `run-AAAAMMDD-HHMMSS-PID`. O Ralph preserva todos os
runs locais e impede duas execuções simultâneas no mesmo repositório:

```text
.phases/
  current                         # ponteiro textual para o último run
  runs/<run-id>/                  # fases, prompts, logs e estado do run
  progress/<input-hash>.progress  # retomada segura para o mesmo PHASES.md
  .ralph.lock/                    # lock enquanto um Ralph está ativo
```

O `.progress` legado é importado somente quando seu stamp é compatível com o
documento atual. O Gate 3 continua sendo a autoridade final sobre cada task.

### Monitor web local

Além do TUI `ralph-watch.sh`, o monitor web read-only acompanha a execução e o
histórico sem controlar o Ralph:

```bash
./scripts/ralph-web.sh /caminho/do/projeto
# http://127.0.0.1:7331
```

Ele usa Python 3 e HTML/CSS/JavaScript sem dependências externas, atualiza a
tela a cada segundo e aceita apenas loopback. Expõe as rotas versionadas
`/api/v1/runs`, `/api/v1/runs/current`, `/api/v1/runs/{id}` e
`/api/v1/runs/{id}/logs?after=<offset>`. Não há CORS, bind público ou rotas de
iniciar, cancelar, pausar ou retomar execução.

Para um procedimento completo dos três fluxos (ajuste, funcionalidade em
produção e projeto novo), consulte [o guia PDF](output/pdf/guia-devworks-ralph.pdf).

### Roteiro prático: projeto existente sem Harness instalado

Os comandos abaixo são executados <strong>na raiz do projeto que receberá a
funcionalidade</strong>. Substitua `/caminho/devworks-harness` pelo local onde
este repositório foi clonado e substitua o comando de testes pelo comando real
do seu sistema.

```bash
# 1. Entrar no projeto e confirmar que é um repositório Git.
cd /caminho/do/meu-projeto

# 2. Criar uma branch isolada para a funcionalidade.
git switch -c feat/minha-funcionalidade

# 3. Autenticar e verificar a CLI que executará os agentes.
codex login
codex --version

# 4. Copiar os Skills DEVWORKS para este projeto.
/caminho/devworks-harness/scripts/install-platform.sh \
  --platform codex --scope project
```

O passo 1 confirma que nenhum trabalho alheio será incluído. O passo 2 isola o
resultado. O passo 3 autentica e confirma a CLI instalada. O passo 4 usa o
diretório nativo da engine (para Codex, `.agents/skills/`), sem copiar
dependências de frontend ou servidor.

Em seguida, abra o projeto no Codex e envie estes prompts, nesta ordem:

```text
Use o Skill ai-context. Analise o código existente e gere o contexto do projeto.
Não implemente nenhuma funcionalidade.
```

```text
Use o Skill plan para a funcionalidade: <descreva o objetivo, regras,
perfis afetados, critérios de aceite e restrições>. Não implemente código.
```

Quando `PLAN.md` estiver aprovado, detalhe a próxima release:

```text
Use o Skill task-builder para a fase <N> de .spec/features/<slug>.
Não implemente código. Gere o PHASES.md de uma única fase.
```

Revise o `PHASES.md` criado em `.spec/features/<slug>/phases/`. Quando estiver
aprovado, execute a fase; o Ralph preserva as mudanças para sua revisão:

```bash
# 5. Executar as fases.
/caminho/devworks-harness/scripts/ralph.sh \
  --engine codex \
  --test-cmd 'php artisan test' \
  .spec/features/<slug>/phases/<NN>-<nome>/PHASES.md

# 6. Em outro terminal, acompanhar sem controlar a execução.
/caminho/devworks-harness/scripts/ralph-web.sh .
```

Abra `http://127.0.0.1:7331`. Ao terminar, revise o diff completo, execute o
teste manual do requisito e faça o commit que desejar antes do deploy. Para um
projeto sem Git, inicialize um repositório antes do passo 2.

**Pré-requisitos do ralph.sh:**

- Engine Codex: `npm install -g @openai/codex`
- Engine Claude: `npm install -g @anthropic-ai/claude-code`
- Engine OpenCode: CLI estável `opencode`, instalado e autenticado ([instalação](https://opencode.ai/docs))
- Engine Antigravity: CLI `agy`, instalado e autenticado ([instalação](https://antigravity.google/docs/cli/install/))
- Raiz de um repositório git com árvore de trabalho **limpa**

## Comandos

### `/init` — roteador da cadeia init

Mostra o estado dos artefatos de `.spec/init/` (presente / ausente / desatualizado) e **invoca o próximo comando da cadeia** (um passo por execução — re-rode `/init` para avançar). Não escreve nada por conta própria; toda autoria vive no comando `init:*` invocado.

A cadeia, em ordem:

| # | Artefato | Comando | Insumos |
|---|---|---|---|
| 1 | `.spec/init/project-description.md` | `/init:project-description` | — (cabeça da cadeia) |
| 2 | `.spec/init/user-stories.md` | `/init:user-stories` | project-description |
| 3 | `.spec/init/database-schema.md` | `/init:database-schema` | description + stories |
| 4 | `.spec/init/project-phases.md` | `/init:project-phases` | description + stories + schema |
| — | `.spec/init/design/` | manual (opcional) | — |

Cada artefato gerado carrega na linha 3 um **stamp** dos insumos (`arquivo@sha256:<12 chars>`). Se um insumo mudar depois, o `/init` detecta e reporta o downstream como *stale* — re-rodar o comando correspondente é upsert-safe: ele entrevista só sobre os deltas e atualiza o stamp.

- **`/init:project-description`** — entrevista o desenvolvedor, descobre a stack e produz a descrição estruturada do projeto.
- **`/init:user-stories`** — deriva user stories estruturadas e testáveis da descrição.
- **`/init:database-schema`** — deriva um schema de banco sugerido em DBML.
- **`/init:project-phases`** — planeja a construção em fases numeradas, agent-ready, com tasks, acceptance criteria e feature tests. **É o input padrão do `ralph.sh`.** Lê `.spec/init/design/` quando existir (refs de telas/componentes).

### `/plan` — pipeline de planejamento de feature

Os comandos abaixo descrevem a interface legada do plugin Claude. No fluxo
portável, o Skill `plan` produz `SPEC.md` e `PLAN.md`; após a aprovação, o
Skill `task-builder` cria o `PHASES.md` da release escolhida.

```
/plan "<descrição da feature ou caminho para arquivo de descrição>"
```

Produz, sob `.spec/features/<slug>/`:

| Artefato | Conteúdo |
|---|---|
| `SPEC.md` | Especificação formal em GEARS, com seções RIGID/FLEXIBLE, diagramas AS IS / TO BE e acceptance criteria binários |
| `PLAN.md` | Decomposição de tasks consciente da arquitetura, com fases de dependência, riscos e critérios de validação |
| `PHASES.md` | Saída de compatibilidade do comando Claude; no fluxo portátil, é gerado por `task-builder` para uma fase específica |
| `openapi.yaml` / `service.proto` / `asyncapi.yaml` | Contratos formais, quando a SPEC declara superfície de API (condicional) |

Características:

- **Sem issue tracker** — a descrição confirmada + ACs são a fonte de verdade. Nada de Jira.
- **Tier de complexidade** (`light` / `standard` / `complete`) classificado por sinais objetivos (nº de requisitos, multi-repo, contratos, mensageria); ajusta a profundidade da SPEC, a obrigatoriedade do clarifier e a emissão de contratos.
- **Checkpoints humanos** em cada etapa: confirmação do input normalizado, aprovação da SPEC, resolução de ambiguidades, confirmação da decomposição.
- **Clarifier em duas fases** — o agente analisa a SPEC e devolve perguntas priorizadas; o roteador as apresenta ao desenvolvedor e re-invoca o agente com as respostas, que atualiza a SPEC in-place.
- **Gate de arquitetura** — exige `AGENTS.md` / `docs/agents/` (ou avisa e marca `architecture_reference_status: missing`). Sem contexto de arquitetura o pipeline nunca planeja em silêncio.
- **Nunca escreve código de aplicação.** O fechamento aponta o handoff de execução:

```bash
./ralph.sh .spec/features/<slug>/PHASES.md
```

No fluxo portátil, passe ao Ralph o caminho criado pelo Task Builder:

```bash
./scripts/ralph.sh .spec/features/<slug>/phases/<NN>-<nome>/PHASES.md
```

### `/ai-context` — árvore de contexto canônica

```
/ai-context [path] [+id] [-id] [--adopt]
```

Gera ou atualiza 10 artefatos a partir do **código implementado** (nunca lê `.spec/`):

| Artefato | Conteúdo |
|---|---|
| `AGENTS.md` | 6 seções: comandos, convenções, regras comportamentais, setup, referências, índice de docs |
| `CLAUDE.md` | Redirect ≤ 400 bytes para AGENTS.md |
| `docs/agents/project_overview.md` | Propósito, consumidores, fluxo macro |
| `docs/agents/architecture.md` | Estilo, layout, responsabilidades por camada |
| `docs/agents/tech_stack.md` | Linguagem, framework, runtime, tooling de teste |
| `docs/agents/coding_guidelines.md` | ≥ 3 padrões observados + enforcement |
| `docs/agents/domain_rules.md` | Regras de negócio como implementadas |
| `docs/agents/api_contracts.md` | Endpoints, payloads, formatos de mensagem |
| `docs/agents/data_model.md` | Entidades, storage, migrations |
| `docs/agents/dependencies.md` | Serviços externos, libs internas, infra compartilhada |

Regras centrais:

- **Idempotente** — upsert seguro; re-rodar atualiza só o que sofreu drift.
- **Documenta a realidade (AS IS)** — código, manifests, CI e configs são as únicas fontes; nunca inventa, nunca prescreve.
- **Contrato de ownership** — todo arquivo gerado carrega banner na linha 3. Arquivo sem banner (escrito à mão) nunca é sobrescrito; `--adopt` incorpora as regras concretas dele à árvore gerada e assume a posse.
- **Preserva blocos de terceiros** — regiões `<tag>...</tag>` (ex.: Laravel Boost) são re-anexadas verbatim na regeneração.
- Filtros `+id` / `-id` geram só um subconjunto (ex.: `/ai-context +AGENTS +architecture`).

## `scripts/ralph.sh` — orquestrador de execução

Lê um documento de fases, quebra pelo heading `## Phase N: <título>` e alimenta cada fase a uma sessão **nova** do Codex CLI, Claude Code, OpenCode ou Antigravity, sem interação humana, do início ao fim. O Ralph, os Skills e o monitor fazem parte do DEVWORKS Harness e não dependem de recursos exclusivos de uma plataforma.

Consulte também o [guia operacional dos quatro engines](docs/guia-ralph-quatro-engines.md).

```bash
./scripts/ralph.sh [opções] [caminho-do-arquivo]
```

Sem argumento, resolve o input nesta ordem: `.spec/init/project-phases.md` → `.spec/project-phases.md` (layout pré-init, com aviso). Um `PHASES.md` de feature também é input válido.

> **Nota sobre autonomia e permissões**: Ralph é um orquestrador não assistido. As sessões de implementação são autônomas: Codex usa `danger-full-access`, Claude usa `--dangerously-skip-permissions`, OpenCode usa `run --auto` e Antigravity usa `accept-edits` com `--dangerously-skip-permissions`. Rode apenas em repositórios confiáveis, de preferência em branch descartável ou ambiente isolado (container/VM). Ralph não faz stage, commit, reset nem altera exclusões do Git; revise o diff acumulado e faça o commit manualmente. O Gate 3 é restrito: Codex é somente leitura; Claude permite apenas `Read,Glob,Grep`; a configuração inline do OpenCode nega tudo exceto read/glob/grep; Antigravity usa `--mode plan --sandbox`, sem a flag perigosa.

### Invariantes

1. Cada fase **e** cada ciclo de correção roda em sessão nova, com prompt auto-contido. Nunca reutiliza sessão.
2. Zero perguntas — execução totalmente autônoma.
3. Fase só é "completa" quando passa pelos **4 gates mecânicos**, nunca pelo exit code do engine.
4. Limite de uso da API → espera o reset e re-executa a **mesma** fase, sem consumir ciclo de correção.
5. **Sem escrita no Git** — fases deixam as mudanças na árvore para revisão e commit manual.

### Os 4 gates

| Gate | Pergunta | Como decide |
|---|---|---|
| 0 | O engine terminou de verdade? | codex: exit code; claude: JSON de resultado bem-sucedido; opencode: exit code 0, sem evento terminal de erro e com `step_finish`; antigravity: exit code 0 e `result.status: SUCCESS` final |
| 1 | A sessão escreveu código? | Assinatura da árvore antes/depois. **Sinal, não veredito** — fase já implementada faz o engine (corretamente) não escrever nada; o sinal alimenta a causa do ciclo de correção |
| 2 | A suite de testes passa? | Rodada **pelo ralph**, fora da sessão do agente — o agente não pode "mentir verde" |
| 3 | Cada task está de fato no código? | Sessão verificadora independente e restrita, que emite `TASK <n>: DONE/INCOMPLETE` por task. Roda em toda fase por default (`RALPH_VERIFY=always`); `RALPH_VERIFY_MODEL` seleciona opcionalmente o modelo |

Qualquer gate vermelho → **ciclo de correção**: sessão nova recebe a fase inteira + a causa real da falha (nunca "os testes falharam" genérico). Default: 3 ciclos por fase.

Gates verdes marcam a fase como concluída; as mudanças ficam na árvore de trabalho.

### Detecção do comando de teste (gate 2)

Primeira regra que resolver: `--test-cmd` → `RALPH_TEST_CMD` → detecção por manifest (Laravel Sail → `composer test` → `php artisan test` → `npm test` → `pytest` → `go test ./...` → `cargo test`) → nada resolvido = gate 2 pulado com aviso alto (gate 3 segura sozinho).

Projeto Laravel Sail: a suite roda **dentro do container** (`vendor/bin/sail test`); containers parados abortam no preflight — todo gate 2 falharia e queimaria ciclos à toa.

### Opções e variáveis

| Opção | Efeito |
|---|---|
| `--engine codex\|claude\|opencode\|antigravity` | Engine de implementação (default: `codex`; Antigravity chama `agy`) |
| `--profile routine\|standard\|complex` | Perfil da política de modelos do Antigravity (default: `standard`) |
| `--from N` | Começa na fase N (limpa o progresso das fases ≥ N) |
| `--keep-going` | Continua após fase falhar, preservando o trabalho parcial na árvore (default: para) |
| `--max-cycles N` | Ciclos de correção por fase (default: 3) |
| `--test-cmd "<cmd>"` | Comando de teste do projeto (gate 2) |
| `--no-verify` | Desliga o gate 3 |
| `--dashboard` | Painel ao vivo no terminal (ver abaixo) |

| Variável | Efeito |
|---|---|
| `RALPH_TEST_CMD` | Comando de teste (gate 2) |
| `RALPH_VERIFY` | Gate 3: `always` (default) \| `auto` (economiza: só quando o gate 2 não basta) \| `off` |
| `RALPH_VERIFY_MODEL` | Modelo opcional do verificador (`sonnet` é o default do Claude) |
| `RALPH_EXECUTION_PROFILE` | Perfil Antigravity: `routine`, `standard` ou `complex` |
| `RALPH_IMPLEMENTATION_MODEL` | Fixa um modelo Antigravity e desliga o fallback de modelo |
| `RALPH_MODEL_POLICY` | Caminho alternativo para a política de modelos |
| `RALPH_MAX_CYCLES` | Ciclos de correção por fase (default: 3) |
| `RALPH_MAX_LIMIT_WAITS` | Esperas consecutivas por limite de uso, por fase (default: 20) |
| `RALPH_LIMIT_WAIT_DEFAULT` | Fallback de espera em segundos (default: 1800) |
| `RALPH_LIMIT_BUFFER` | Segundos extras após o reset (default: 60) |
| `RALPH_ANTIGRAVITY_TIMEOUT` | `agy --print-timeout` por sessão (default: `30m`) |

Durante cada sessão, o ralph exporta `RALPH_ENGINE`, `RALPH_PHASE_TITLE`, `RALPH_PHASE_NUM`, `RALPH_PHASE_TOTAL`, `RALPH_PHASE_ATTEMPT` e `RALPH_PHASE_MAX_ATTEMPTS` — úteis para hooks de notificação (ex.: n8n).

### Estado e progresso

O trabalho interno fica em `.phases/`: `current` aponta para o run selecionado,
`runs/<run-id>/` preserva fases, prompts, estado e logs, e
`progress/<input-hash>.progress` retoma somente o mesmo input. Um
`.phases/.progress` legado compatível é importado uma vez. Um lock por
repositório impede dois Ralphs simultâneos.

Exit code: `0` = todas as fases verdes; `1` = alguma falhou ou abortou.

## `scripts/ralph-watch.sh` — painel ao vivo

O ralph publica o estado do run em `.phases/state/` **sempre**, com ou sem `--dashboard`. O `ralph-watch.sh` lê esse estado e desenha o painel:

```bash
./scripts/ralph.sh --engine claude --dashboard   # painel no próprio terminal
./scripts/ralph-watch.sh /caminho/do/repo        # painel de outro terminal
```

```
┌─────────────────── PROGRESSO ───────────────────┐ ┌──────────────── TRABALHO ATUAL ─────────────────┐
│ Fases  1/2      [███████████░░░░░░░░░░░░]  50%  │ │ Fase:      2 · Interface observável             │
│ Tasks  1/2      [███████████░░░░░░░░░░░░]  50%  │ │ Ciclo:     1/3    Gate: G2                      │
└─────────────────────────────────────────────────┘ └─────────────────────────────────────────────────┘
┌──────┬────────────────────────────────────────────┬────────────────┬───────────┬─────────────────────┐
│ F1   │ Preparação                                 │ ✓ Concluída    │ 1         │ G0 ✓ G1 ✓ G2 ✓ G3 ✓ │
│ F2   │ Interface observável                       │ ▶ Em execução  │ 1         │ G0 ✓ G1 ✓ G2 ⋯ G3 · │
│ T1   │   ↳ renderizar títulos longos              │ ✓ Concluída    │ –         │ –                   │
│ T2   │   ↳ cobrir falhas de rede com retry        │ ▶ Em execução  │ –         │ –                   │
└──────┴────────────────────────────────────────────┴────────────────┴───────────┴─────────────────────┘
```

### De onde vem o progresso por task

Uma fase é **uma** sessão de agente, então o ralph não teria como saber onde a sessão está — a menos que a sessão conte. Claude, OpenCode e Antigravity expõem saída linha a linha enquanto trabalham:

Claude usa `--output-format stream-json`, OpenCode usa `run --format json` e Antigravity usa `--output-format stream-json`. O Ralph lê esses streams e reescreve o progresso em `.phases/state/live.tsv`, de quatro fontes, nesta ordem de precedência:

1. **Marcadores de texto** (fonte primária). O prompt manda o agente escrever, como linha isolada, `RALPH-TASK <n> START` antes de começar o item *n* e `RALPH-TASK <n> DONE` quando ele estiver pronto. É texto puro: **não depende de ferramenta nenhuma** — e isso é o que importa, porque em sessão headless (`claude -p`) as ferramentas de lista de tarefas simplesmente não existem, mesmo que o agente tente carregá-las com `ToolSearch`.
2. **Lista de tarefas do agente**, quando a sessão tiver uma (`TaskCreate`/`TaskUpdate` ou `TodoWrite`): as transições `in_progress`/`completed` viram progresso.
3. **Reserva observacional** — sem marcador e sem lista, o ralph deduz pelo que o agente edita. Um plano do `/plan` declara `Arquivos:` em cada item, e é esse casamento (caminho editado ↔ arquivo declarado pela task) que dá a granularidade; sem a declaração, cai no enunciado da task. Ao entrar numa task, as anteriores contam como concluídas — o agente trabalha em ordem, e nem toda task tem arquivo próprio.
4. **Sinal de vida**: assim que a sessão abre, a task 1 aparece em execução — nunca uma fase inteira parada em "Pendente".

No fim da fase, o **gate 3 tem a palavra final**: o veredito `TASK <n>: DONE/INCOMPLETE` do verificador sobrepõe marcador, lista e dedução. Uma task marcada como pronta que não está no código aparece como `! Incompleta`.

Ou seja: durante a fase o painel mostra a intenção do agente; ao fim da fase mostra a verdade verificada.

No engine **codex** não há stream equivalente — a granularidade fica por fase, e as tasks aparecem como pendentes até o veredito do gate 3.

### Planos grandes: topo fixo e tabela rolante

Com dezenas de tasks a tabela não cabe na tela. O painel então mantém **o topo fixo** (identificação, barras, trabalho atual) e faz a tabela de fases e tasks rolar dentro de uma janela do tamanho do terminal — com barra de rolagem na borda direita e um rodapé dizendo quanto ficou fora:

```
  ▲ 23 acima · ▼ 9 abaixo · seguindo a fase atual · ↑↓ PgUp/PgDn rolam · f segue a fase
```

A linha em execução — fase e task — fica **realçada de ponta a ponta**, para ser achada de relance na tabela cheia.

Por padrão a janela **segue a fase corrente**: mostra o bloco da fase inteiro quando ele cabe e centra a task em execução quando não cabe. As teclas abaixo assumem o controle a qualquer momento e valem também com `--dashboard`, com o painel embutido no ralph:

| Tecla | Efeito |
|---|---|
| `↑` `↓` ou `k` `j` | Rola uma linha |
| `PgUp` `PgDn`, `b` ou espaço | Rola uma página |
| `Home`/`g` e `End`/`G` | Primeira e última linha |
| `f` | Volta a seguir a fase corrente |
| `q` | Sai do painel (só no modo avulso; não interrompe o ralph) |

| Opção do watch | Efeito |
|---|---|
| `--once` | Desenha um frame e sai (útil em script/CI); dump completo, sem recorte |
| `--interval N` | Segundos entre frames (default: 1) |
| `--no-color` | Desliga ANSI |
| `--color` | Força ANSI mesmo sem terminal (teste, arquivo) |
| `RALPH_WATCH_COLS` | Fixa a largura, para terminal que não reporta |
| `RALPH_WATCH_LINES` | Fixa a altura; com `--once` também liga a janela rolante |

Com `--dashboard`, as linhas de log do ralph vão para `.phases/logs/ralph.log` (o painel é dono da tela) e o relatório final é impresso no terminal ao sair. Sem o `ralph-watch.sh` ao lado do `ralph.sh`, o `--dashboard` avisa e segue no modo de log — o `ralph.sh` continua sendo copiável sozinho para outro repositório.

## `scripts/ralph-web.sh` — monitor web local

O monitor somente leitura mostra o estado corrente e o histórico do projeto em
uma interface responsiva inspirada em terminal. Usa Python 3 e
HTML/CSS/JavaScript estático, escuta apenas no loopback e não oferece CORS nem
rotas de controle.

```bash
./scripts/ralph-web.sh /caminho/do/repo
# Ralph Web: http://127.0.0.1:7331
```

Rotas JSON: `/api/v1/runs`, `/api/v1/runs/current`, `/api/v1/runs/{id}` e
`/api/v1/runs/{id}/logs?after=<offset>`.

### Contrato de formato do input

Validado no preflight:

- ≥ 1 heading `## Phase N: <título>`
- Nenhum heading `## Phase ...` fora desse formato (heading torto some silenciosamente do run — o preflight aborta antes de gastar tokens)
- Sub-fases em `### Phase N.M:` (não viram sessão própria)
- Qualquer outro `## ` encerra a captura da fase anterior

## Agentes

Os comandos são **roteadores finos** — todo conhecimento de template vive nos agentes:

| Agente | Pipeline | Papel |
|---|---|---|
| `specifier` | `/plan` §5 | Descrição confirmada + ACs → SPEC.md formal (GEARS, RIGID/FLEXIBLE) |
| `clarifier` | `/plan` §6 | QA adversarial de requisitos: analisa ambiguidades, resolve com as respostas do dev |
| `planner` | `/plan` §7 | Adaptador legado Claude: SPEC → PLAN.md + PHASES.md + contratos; read-only sobre o código |
| `ai-context-inspector` | `/ai-context` §3 | Varredura read-only do repo → digest estruturado |
| `ai-context-core` | `/ai-context` §4 | Digest → `AGENTS.md` + `CLAUDE.md` |
| `ai-context-docs` | `/ai-context` §4 | Digest → 8 arquivos `docs/agents/*.md` |

Os dois writers de `/ai-context` rodam em paralelo (arquivos disjuntos, digest read-only).

## Estrutura do repositório

```
.claude-plugin/plugin.json     manifest do plugin
commands/
  init.md                      /init (roteador diagnóstico)
  init/                        /init:project-description, user-stories,
                               database-schema, project-phases
  plan.md                      /plan (roteador do pipeline de planejamento)
  ai-context.md                /ai-context (roteador da árvore de contexto)
agents/                        specifier, clarifier, planner,
                               ai-context-{inspector,core,docs}
scripts/
  ralph.sh                     orquestrador de execução por fases
  ralph-watch.sh               painel ao vivo do run (lê .phases/state/)
  test-ralph.sh                suite red/green do ralph com engine mock
  check-init-drift.sh          guarda contra drift textual das regras
                               duplicadas nos comandos init
  check-shell.sh               bash -n + shellcheck em scripts/*.sh
docs/plans/                    planos de hardening internos do harness
```

## Desenvolvimento

```bash
scripts/test-ralph.sh        # suite do ralph.sh — binários fake `claude`/`codex`/`opencode`/`agy`
                             # no PATH, zero rede, zero token; exit 0 = verde
scripts/test-ralph.sh <caso> # roda um caso específico
scripts/check-shell.sh       # bash -n em todos os scripts + shellcheck se disponível
scripts/check-init-drift.sh  # âncoras verbatim das regras compartilhadas dos init:*
```

`test-ralph.sh` exige Bash 4+ (usa arrays associativos); o Bash 3.2 do macOS
basta para `scripts/check-shell.sh`, mas não para a suite funcional.

Sobre o `check-init-drift.sh`: os quatro `commands/init/*.md` **inlinam de propósito** as mesmas regras de entrevista, idioma, re-run e staleness — comandos de plugin precisam ser auto-contidos em runtime (executam dentro do projeto do desenvolvedor, onde a raiz do plugin não é alcançável via `@`-includes). O custo dessa duplicação é drift silencioso; o script torna o drift barulhento.

## Princípios de design

- **Roteadores finos, agentes donos do conteúdo** — comandos orquestram, verificam artefatos em disco e reportam; nunca autoram SPEC/PLAN/docs.
- **Confie, mas verifique** — todo artefato entregue por agente é validado mecanicamente (existência, headings, contagens) pelo roteador.
- **Realidade ≠ intenção** — `/ai-context` documenta só o implementado; `.spec/` é invisível para ele. A cadeia `.spec/` documenta a intenção.
- **Sem escrita no Git** — o desenvolvedor revisa com `git diff` e commita manualmente; o `ralph.sh` não faz stage, commit, reset ou altera exclusões do Git.
- **Sem segredos** — `.env` nunca é lido; nomes de variáveis vêm de `.env.example`.
- **Staleness explícita, nunca bloqueante** — stamps sha256 detectam insumos desatualizados; a decisão é sempre do desenvolvedor.
