---
name: init
description: Descobre ou estrutura a especificação inicial de um projeto antes do planejamento. Use em projetos novos para transformar uma ideia em documentos de contexto, histórias, esquema sugerido e mapa de releases.
---

# Inicializar a especificação do projeto

Crie ou atualize o contexto de produto em `.spec/init/`. Este workflow não
escreve código de aplicação, não executa migrations e não faz commits.

## Entradas

- Ideia, PRD ou caminho de um documento fornecido pela pessoa desenvolvedora.
- Repositório alvo, que pode estar vazio ou já conter código inicial.

## Antes de escrever

1. Leia `README*`, manifestos, arquivos de CI, exemplos de ambiente e a árvore
   do repositório. Não leia arquivos `.env` nem exponha segredos.
2. Se `.spec/init/` já existir, leia seus documentos primeiro. Eles são decisões
   do projeto: preserve texto e identificadores que a pessoa tenha alterado.
3. Pergunte somente pelo que muda escopo, prioridade, regras de negócio ou
   arquitetura. Registre o que continuar em aberto; não invente decisões.

## Artefatos e ordem

Gere na ordem abaixo. Atualize documentos existentes por edição localizada e
preserve IDs, numeração e conteúdo removido pela pessoa usuária.

| Ordem | Arquivo | Deve conter |
|---|---|---|
| 1 | `.spec/init/project-description.md` | visão do produto, conceitos, stack detectada, fluxos e dúvidas abertas |
| 2 | `.spec/init/user-stories.md` | personas, histórias `US-N.N`, prioridade e critérios de aceite testáveis |
| 3 | `.spec/init/database-schema.md` | esquema sugerido em DBML, relações, tabelas auxiliares e premissas |
| 4 | `.spec/init/project-phases.md` | mapa de releases/fases, dependências, corte de MVP e rastreabilidade |

Use a língua do PRD. Registre a origem detectada de cada informação técnica.
Quando o projeto ainda não possui código, marque a stack como proposta a ser
confirmada, em vez de afirmá-la como fato.

### Regras de cada artefato

**Descrição do projeto**

- Título: `# <Projeto> — Project Description`.
- Inclua `## Overview`, `### Key Concepts`, `## Tech Stack` e
  `## Core Workflows` com ao menos um fluxo numerado.
- Conceitos definem vocabulário e regras; fluxos descrevem início, sucesso,
  erro e limites relevantes.

**Histórias de usuário**

- Use `### US-N.N: <título>` e a forma `As a / I want to / So that`.
- Toda história possui checklist de critérios concretos, resultado esperado,
  prioridade `High`, `Medium` ou `Low` e uma linha no apêndice de status.
- Mapeie todo fluxo da descrição para uma história ou registre explicitamente
  que ele foi excluído por decisão da pessoa usuária.

**Esquema sugerido**

- Não trate o documento como migration nem altere o banco.
- Modele tabelas, chaves, nulidade, índices e relações em bloco `dbml`.
- Prefira tabelas auxiliares para conjuntos fechados de valores, registre dados
  derivados e diferencie fatos detectados de decisões propostas.

**Fases do projeto**

- São releases em alto nível, não tarefas de implementação.
- Ordene fundação antes de fluxos de produto e mantenha cada fase pequena o
  suficiente para ser detalhada separadamente.
- Use somente headings `## Phase N: <título>` para fases executáveis pelo
  Ralph; subfases, se existirem, usam `### Phase N.M: <título>`.
- Inclua objetivo, dependências, histórias/tabelas/fluxos cobertos, risco e
  definição de pronto de cada fase. Não preencha checkboxes de tarefas aqui.

## Validação

Antes de encerrar, confira:

```sh
test -s .spec/init/project-description.md
test -s .spec/init/user-stories.md
test -s .spec/init/database-schema.md
test -s .spec/init/project-phases.md
grep -Eq '^### US-[0-9]+\.[0-9]+:' .spec/init/user-stories.md
grep -Eq '^## Phase [0-9]+: ' .spec/init/project-phases.md
grep -q '^```dbml' .spec/init/database-schema.md
```

Relate os arquivos produzidos, decisões ainda em aberto e a fase indicada para
o primeiro ciclo. Em seguida, use `task-builder` para detalhar somente a fase
que será executada.
