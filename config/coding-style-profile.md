# Guia Universal de Estilo e Engenharia

Este perfil define preferências de engenharia para projetos que usam o
DEVWORKS Harness. Ele é agnóstico de linguagem, framework e ferramenta.

Antes de alterar código, o agente deve identificar a stack, suas versões, os
formatadores e linters configurados, as regras locais e trechos semelhantes já
implementados. A documentação oficial aplicável à versão detectada deve orientar
as decisões técnicas. Quando ela não estiver acessível, o agente deve registrar
essa limitação e usar somente evidências verificadas no projeto.

As regras deste perfil expressam a intenção desejada. Elas não provam que o
projeto já as adota e não substituem convenções, contratos ou formatadores que
o próprio projeto imponha.

## 1. Escopo e simplicidade

- Resolva a causa no menor ponto de mudança necessário. Preserve contratos,
  dados e fluxos não relacionados.
- Não introduza camadas, dependências, validações ou consultas redundantes sem
  uma necessidade confirmada pelo código, pela stack ou pelo requisito.
- Não reformate arquivos inteiros nem altere código fora do escopo.
- Prefira APIs, mecanismos de segurança e validações já fornecidos pela stack e
  já usados no projeto.

## 2. Legibilidade do fluxo

- Mantenha condições curtas e fáceis de ler. Quando uma condição reunir regras
  independentes, extraia valores ou verificações nomeadas e divida os `if`s sem
  mudar a lógica, a ordem ou os efeitos colaterais.
- Indente de acordo com o arquivo e com o formatador configurado. Nunca misture
  estilos de indentação na mesma alteração.
- Separe etapas distintas do processamento por linhas em branco: obtenção de
  dados, transformação, decisão, efeito externo e retorno. Após uma consulta,
  leitura ou chamada relevante, deixe uma linha em branco antes da próxima
  etapa quando isso tornar o fluxo mais claro.
- Use retornos antecipados ou a estrutura equivalente da linguagem quando eles
  reduzirem aninhamento e preservarem a clareza.
- Evite `break`, `continue` e equivalentes de salto de fluxo. Use-os somente
  quando a alternativa deixar o código menos claro ou mais propenso a erro.

## 3. Funções e chamadas

- Toda função, método, handler ou unidade equivalente criada deve ter uma breve
  descrição no formato de documentação adotado pelo projeto e pela linguagem.
- Não crie uma função intermediária que apenas chame outra. Faça o chamador usar
  diretamente a função final quando não houver transformação, política,
  tratamento de erro, limite de responsabilidade ou contrato público a manter.
- Prepare valores, objetos e coleções antes da chamada. Evite passar expressões
  extensas, múltiplas transformações ou estruturas montadas inline como
  argumentos, salvo quando o padrão local tornar a chamada mais clara.

## 4. Alinhamento e formatação

- Quando a linguagem, o formatador e o estilo local permitirem, alinhe
  atribuições e associações de mapas/arrays em blocos relacionados para facilitar
  a leitura.
- Não force alinhamento que conflite com um formatador obrigatório, uma regra de
  lint ou o estilo predominante do arquivo.

## 5. Descoberta de padrões por projeto

Para cada mudança, verifique nesta ordem:

1. regras locais, documentação, manifestos, versões e ferramentas configuradas;
2. documentação oficial da stack e da versão relevantes à mudança;
3. pelo menos um trecho semelhante no código, quando houver;
4. contratos públicos, testes e convenções de nomenclatura existentes.

Exemplos como Joomla, Laravel, Component Creator ou outro gerador não são
regras globais. Quando estiverem presentes, seus nomes de diretórios, arquivos,
classes, convenções de assets e pontos de extensão devem ser descobertos e
seguidos no projeto correspondente.
