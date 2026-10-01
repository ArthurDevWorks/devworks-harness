---
name: plan
description: Planeja uma mudança sem implementar código. Use após receber um PRD, requisito ou pedido de manutenção para produzir SPEC.md e PLAN.md com releases, riscos e critérios de aceite.
---

# Planejar uma mudança

Transforme uma necessidade em especificação e plano de releases. Escreva
somente em `.spec/features/<slug>/`; não altere código, dependências, banco,
arquivos de ambiente, Git ou infraestrutura.

## Entrada e contexto

1. Receba descrição livre ou caminho para um PRD/requisito. Se estiver vazio,
   solicite a descrição antes de continuar.
2. Crie `<slug>` em kebab-case, com até 50 caracteres.
3. Leia primeiro `AGENTS.md` e `docs/agents/` quando existirem. Em projetos
   novos, leia `.spec/init/`. Em projetos legados sem contexto, pare e recomende
   executar `ai-context` primeiro.
4. Leia apenas os arquivos necessários para confirmar o estado atual. Nunca
   leia `.env` ou credenciais.

## Processo

1. Extraia requisitos funcionais, não funcionais, limites, integrações,
   dependências e critérios de aceite. Marque como `draft` critérios deduzidos
   que ainda não foram confirmados.
2. Antes de criar os artefatos, apresente um resumo curto: escopo, exclusões,
   critérios, slug e riscos. Confirme somente dúvidas que mudem a solução.
3. Escreva ou atualize os dois documentos abaixo. Em nova execução, preserve
   decisões, IDs e texto manual que ainda seja válido; não reconstrua tudo sem
   necessidade.

| Arquivo | Papel |
|---|---|
| `.spec/features/<slug>/SPEC.md` | contrato da mudança: comportamento atual, comportamento desejado, requisitos, critérios de aceite, não escopo, riscos e decisões abertas |
| `.spec/features/<slug>/PLAN.md` | fases/releases, dependências, áreas de código afetadas, estratégia de testes, rollback e definição de pronto |

## Formato mínimo

`SPEC.md` começa com `# SPEC:` e contém `## RIGID` (regras não negociáveis),
`## TO BE` (resultado esperado), critérios de aceite binários e uma seção de
dúvidas abertas quando houver.

`PLAN.md` começa com `# Implementation Plan` e contém `## Tasks`, porém as
entradas são de alto nível: uma fase/release, objetivo, dependências, riscos e
cobertura. As tarefas pequenas são responsabilidade do `task-builder`.

Uma fase é adequada quando pode ser revisada, validada e commitada como uma
unidade. A ordem deve respeitar dados/contratos/base antes de interface ou
fluxos que dependam deles.

## Regras para manutenção em legado

- Diferencie comportamento observado de hipótese.
- Referencie caminhos e testes reais que sustentam o plano.
- Preserve contratos públicos, dados existentes e fluxos não relacionados.
- Planeje migrações, compatibilidade e rollback somente quando a evidência
  indicar necessidade.

## Saída e próximo passo

Não produza `PHASES.md` detalhado neste workflow. Depois da aprovação humana
do plano, execute `task-builder` com o slug e o número da release escolhida.
Ele cria o arquivo que o Ralph consome.

## Validação

```sh
test -s .spec/features/<slug>/SPEC.md
test -s .spec/features/<slug>/PLAN.md
head -1 .spec/features/<slug>/SPEC.md | grep -q '^# SPEC:'
head -1 .spec/features/<slug>/PLAN.md | grep -q '^# Implementation Plan'
grep -q '^## RIGID' .spec/features/<slug>/SPEC.md
grep -q '^## TO BE' .spec/features/<slug>/SPEC.md
grep -q '^## Tasks' .spec/features/<slug>/PLAN.md
```

Reporte os caminhos, as fases propostas, os riscos e dúvidas. Pare antes de
qualquer implementação.
