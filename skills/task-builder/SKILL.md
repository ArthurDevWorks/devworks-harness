---
name: task-builder
description: Detalha uma única fase aprovada do PLAN.md em tarefas pequenas, rastreáveis e executáveis pelo Ralph. Use depois de plan e antes de scripts/ralph.sh.
---

# Detalhar uma fase para execução

Converta uma release aprovada em tarefas executáveis pelo Ralph. Não implemente
código, não altere contratos fora da especificação e não faça commits.

## Entrada obrigatória

- Caminho ou slug de `.spec/features/<slug>/`.
- Número da fase/release a detalhar, por exemplo `2`.

Leia `SPEC.md`, `PLAN.md`, `AGENTS.md` e a documentação de arquitetura que
existir. Confirme o estado atual no código apenas para não planejar arquivos,
classes ou integrações inexistentes. Se não localizar a fase no plano, pare e
peça a fase correta; não escolha por conta própria.

## Arquivo de saída

Escreva em:

```
.spec/features/<slug>/phases/<NN>-<slug-da-fase>/PHASES.md
```

`<NN>` usa dois dígitos. Um arquivo contém uma fase; por isso ele pode ser
entregue diretamente ao Ralph sem executar outras releases. Preserve arquivos
de fases anteriores, pois são o histórico de planejamento/executação.

## Formato que o Ralph exige

O conteúdo executável fica integralmente sob uma única heading:

```markdown
# <Produto> — Phase <N>: <Título>

## Phase <N>: <Título>

**Goal:** <resultado observável>
**Depends on:** <nenhuma ou fase/commit necessário>
**Scope:** <limites explícitos>

- [ ] **Task:** <verbo + entrega pequena>
  - **Files:** `<caminho real>`
  - **Change:** <alteração objetiva>
  - **Covers:** <RF, US, tabela, endpoint ou regra>
  - **Acceptance criteria:**
    - <condição binária e verificável>
  - **Tests:** <comando/teste específico, ou `manual: ...` quando justificável>
  - **Risk:** <dados, compatibilidade, efeito externo ou `none`>
```

Não use outro heading `##`. Use `###` apenas para agrupamento dentro da fase.
Não crie tarefas vagas como “implementar feature” nem aceite critérios que não
possam ser verificados.

## Como quebrar as tarefas

- Cada tarefa deve caber em uma execução focada, ter arquivos previstos e um
  resultado independente de revisão.
- Ordene pré-requisitos antes de consumidores. Separe migration, regra de
  negócio, interface e teste quando isso reduzir risco de rollback.
- Todo requisito do escopo da fase deve aparecer em `Covers` de ao menos uma
  tarefa. Todo critério do SPEC deve aparecer em uma tarefa ou ser registrado
  como fora da fase.
- Para regras, cálculos, permissões, validações, estados e APIs, especifique
  teste automatizado. Para trabalho visual puro, descreva uma validação manual
  objetiva e a referência de design, se houver.
- Marque efeitos externos (e-mail, pagamento, deploy, API mutável, migration
  destrutiva) no risco. O Ralph não deve executá-los automaticamente sem a
  aprovação prevista pelo projeto.

## Gate de aprovação

Apresente primeiro a decomposição: quantidade de tarefas, arquivos tocados,
riscos e comandos de teste. Só considere a fase pronta após a aprovação da
pessoa desenvolvedora. Depois dela, a chamada para executar somente esta fase é:

```sh
scripts/ralph.sh .spec/features/<slug>/phases/<NN>-<slug-da-fase>/PHASES.md
```

Quando todas as fases aprovadas já tiverem seus respectivos `PHASES.md`, use o
diretório da feature para executá-las em sequência num único run:

```sh
scripts/ralph.sh .spec/features/<slug>
```

O Ralph descobre `.spec/features/<slug>/phases/*/PHASES.md`, ordena pelos
diretórios e para na primeira falha. `--keep-going` continua após uma falha.

## Validação

```sh
F=.spec/features/<slug>/phases/<NN>-<slug-da-fase>/PHASES.md
test -s "$F"
grep -Eq '^## Phase [0-9]+: ' "$F"
[ "$(grep -c '^## ' "$F")" -eq 1 ]
TASKS="$(grep -cE '^- \[ \] \*\*Task:\*\*' "$F")"; [ "$TASKS" -ge 1 ]
[ "$TASKS" -eq "$(grep -c '^  - \*\*Files:\*\*' "$F")" ]
[ "$TASKS" -eq "$(grep -c '^  - \*\*Change:\*\*' "$F")" ]
[ "$TASKS" -eq "$(grep -c '^  - \*\*Covers:\*\*' "$F")" ]
[ "$TASKS" -eq "$(grep -c '^  - \*\*Acceptance criteria:\*\*' "$F")" ]
[ "$TASKS" -eq "$(grep -c '^  - \*\*Tests:\*\*' "$F")" ]
```

Relate o arquivo criado, tarefas, riscos e comandos de teste. Se todas as fases
da feature já estiverem detalhadas, apresente primeiro o comando único com o
diretório da feature. Não inicie o Ralph automaticamente; a execução é uma
decisão explícita da pessoa usuária.
