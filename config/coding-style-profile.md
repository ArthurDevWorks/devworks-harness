# Guia Canônico de Estilo e Engenharia (DNA de Código)
<!-- DEVWORKS Harness Coding Profile - Baseado nos commits e estilo de desenvolvimento de Arthur Parente -->

Este documento estabelece as diretrizes e padrões de desenvolvimento observados no repositório e nos projetos mantidos. Toda IA, agente ou executor deve seguir rigorosamente estas convenções para produzir código consistente, limpo, cirúrgico e sem retrabalho.

---

## 1. Princípio Fundamental: Simplicidade Cirúrgica vs Over-Engineering

O objetivo da engenharia assistida por IA é **resolver o problema real na causa-raiz com a menor intervenção necessária**, agregando robustez técnica sem criar complexidade acidental.

### O que a IA NUNCA deve fazer:
1. **Proibido Over-Engineering Defensivo em Dados Internos**: Nunca adicione checagens artificiais de tipo (`is_scalar`, `!is_bool`, `filter_var`) em dados internos de models/banco quando a própria plataforma já os valida ou sanitiza.
2. **Proibido Consultas SQL Redundantes**: Nunca faça um `SELECT` manual no banco para checar a existência de um registro antes de chamar um método nativo que já faz exatamente essa consulta (exemplo: rodar SQL em `#__users` antes de chamar `Factory::getUser()`).
3. **Proibido Criar Abstrações Desnecessárias**: Nunca introduza classes de serviço, interfaces, repositórios ou helpers adicionais para uma alteração local de poucas linhas. Respeite o ponto de extensão (`seam`) já adotado no arquivo.
4. **Proibido Reformatar Arquivos Inteiros**: Nunca altere a indentação, quebras de linha ou espaçamento de linhas que não fazem parte do escopo da tarefa.

### O que a IA DEVE agregar:
1. **Tipagem Estrita e Segura (PHP 8.2+)**: Use types explícitos em argumentos e retornos de funções (`array $userIds, int $id): ?object`, `: array`, `: void`.
2. **Prevenção a Injeção de SQL**: Use sempre o Query Builder com `quoteName()` para tabelas e colunas, `quote()` ou casting inteiro `(int)` para valores, e `whereIn()`.
3. **Null-Safety e Defesa Elegante**: Use o operador de coalescência nula (`??`) e safe call (`?->`) em vez de múltiplos blocos `if (isset(...))`.
4. **Early Returns Claros**: Interrompa a execução cedo para casos inválidos (`guard clauses`), separando a guarda da lógica subsequente por uma linha em branco.

---

## 2. Convenções de Código PHP

### 2.1. Abertura de Chaves Allman (`\n{`)
Em métodos, funções e blocos de controle (`if`, `foreach`, `switch`, `while`), a chave de abertura `{` fica **em uma nova linha**, alinhada com a instrução:

```php
// CORRETO (Padrão adotado)
if (!isset($data->user_id))
{
    return;
}

$userId = (int) $data->user_id;
$user   = Factory::getUser($userId);

if (!$user || (int) $user->id !== $userId)
{
    return;
}
```

```php
// ERRADO (Estilo K&R rejeitado)
if (!isset($data->user_id)) {
    return;
}
```

### 2.2. Indentação Fiel ao Arquivo
- **Componentes Joomla (`administrator/`, `components/com_*`, `plugins/`)**: A maioria dos arquivos utiliza **Tabs**. Mantenha tabs onde houver tabs.
- **Projetos Modernos / Laravel / Bibliotecas PSR-12**: Utilize **4 espaços**.
- Nunca misture espaços e tabs na mesma alteração.

### 2.3. Guard Clauses e Sanitização em Linha
Prefira sanitizações concisas e pipes nativos do PHP:

```php
// CORRETO
$userIds = array_values(array_filter(array_unique(array_map('intval', $userIds))));
if (!$userIds)
{
    return [];
}

$enderecos = isset($data['endereco']) && is_array($data['endereco']) ? $data['endereco'] : [];
if ($enderecos !== [])
{
    $this->saveCrmEndereco($enderecos, $idCrm);
}
```

---

## 3. Padrões Joomla 4 e 5 (`com_smart*` e Plugins)

### 3.1. Injeção de Dependências e Acesso ao Banco de Dados
- Utilize o container moderno do Joomla 5 quando disponível:
  ```php
  use Joomla\Database\DatabaseInterface;
  // ou use Joomla\Database\DatabaseDriver;
  $db = Factory::getContainer()->get(DatabaseInterface::class);
  ```
- Monte consultas pelo Query Builder:
  ```php
  $query = $db->getQuery(true)
      ->select($db->quoteName(['id', 'lastvisitDate']))
      ->from($db->quoteName('#__users'))
      ->whereIn($db->quoteName('id'), $userIds);

  $result = $db->setQuery($query)->loadAssocList('id', 'lastvisitDate') ?: [];
  ```

### 3.2. Manipulação de Formulários Joomla
- Ao instanciar e carregar um formulário em sub-operações ou controllers, passe `loadData: false` para não sobrescrever o contexto:
  ```php
  $crmEmailModel = new EmailModel();
  $formCrm       = $crmEmailModel->getForm([], false);
  ```

### 3.3. Textos e Internacionalização
- Sempre utilize `Text::_('CHAVE_SEMANTEICA')` em vez de strings hardcoded em português.
- Adicione a chave correspondente no arquivo `administrator/language/pt-BR/com_*.ini`.

### 3.4. Assets Frontend e Invalidação de Cache (`CRÍTICO`)
- Ao alterar qualquer arquivo JavaScript ou CSS em `media/com_*/js/` ou `media/com_*/css/`, **é obrigatório incrementar a versão do asset no arquivo `media/com_*/joomla.asset.json`**:
  ```json
  {
    "name": "com_smarteventos.inscricaoBe",
    "type": "script",
    "uri": "com_smarteventos/inscricaoBe.js",
    "version": "1.0.2",
    "dependencies": ["jquery"]
  }
  ```
  *Sem essa atualização, os navegadores e clientes continuam servindo o arquivo antigo em cache.*

---

## 4. Convenções Frontend (JavaScript & CSS)

1. **Defensividade Sem Quebra**: Sempre verifique se métodos e objetos opcionais existem antes de invocá-los:
   ```javascript
   if (typeof Joomla.updateCupomVisibility === 'function') {
       Joomla.updateCupomVisibility(Joomla.eventoData);
   }
   ```
2. **Rotas e Parâmetros Nativos**:
   ```javascript
   const url = Joomla.getOptions('system.paths').baseFull + 'index.php?option=com_smarteventos&task=inscricoe.getEventoData&format=json';
   ```
3. **Limpeza de Depuração**: Nunca comite `console.log()` ou `debugger` em código final.

---

## 5. Padrão Canônico de Mensagens de Commit

As mensagens de commit seguem o formato semântico Tridia com contexto de módulo e resumo objetivo:

| Tipo | Prefixo / Emoji | Exemplo |
|---|---|---|
| Correção | `🐛 fix: == <modulo>` | `🐛 fix: == com_smartassociados + correcao para nao atualizar usuario do gestor quando o associado nao tem user.` |
| Ajuste / Melhoria | `👌 style: == <modulo>` | `👌 style: == com_smarteventos + unificando consulta de associado do BE e FE` |
| Nova Funcionalidade | `✨ feat: == <modulo>` | `✨ feat: == com_smartassociados + adicionada geracao de excel com escolha de colunas.` |
| Manutenção / Scripts | `🔧 chore: == <modulo>` | `🔧 chore: == com_smarteventos + atualizacao de versao no asset.json` |
| Refatoração | `♻️ refactor: == <modulo>` | `♻️ refactor: == com_submissoes + otimizacao das buscas pelas submissoes e arquivos.` |

---

## 6. Comparativo Prático: Como Desenvolver vs Over-Engineering

### Caso Real: Validação de Vínculo de Usuário em Salvamento

#### ❌ Como a IA costuma errar (Over-Engineering Rejeitado):
```php
if (!$isNew && $dataCrm
    && isset($dataCrm->user_id)
    && is_scalar($dataCrm->user_id)
    && !is_bool($dataCrm->user_id)
    && filter_var($dataCrm->user_id, FILTER_VALIDATE_INT, ['options' => ['min_range' => 1]]) !== false) {
    $this->updateUser($dataCrm);
}

private function updateUser(object $data) {
    if (!isset($data->user_id) || !is_scalar($data->user_id) || is_bool($data->user_id)) {
        return;
    }
    $userId = filter_var($data->user_id, FILTER_VALIDATE_INT, ['options' => ['min_range' => 1]]);
    if ($userId === false) {
        return;
    }
    $query = $this->db->getQuery(true)
        ->select($this->db->quoteName('id'))
        ->from($this->db->quoteName('#__users'))
        ->where($this->db->quoteName('id') . ' = ' . $userId);
    if (!$this->db->setQuery($query)->loadResult()) {
        return;
    }
    $user = Factory::getUser($userId);
    if (!$user || (int) $user->id !== $userId) {
        return;
    }
    ...
}
```

#### ✅ Como você desenvolve e como a IA deve codar (Aprovado):
```php
if (!$isNew && $dataCrm && isset($dataCrm->user_id))
{
    $this->updateUser($dataCrm);
}

private function updateUser(object $data): void
{
    if (!isset($data->user_id))
    {
        return;
    }

    $userId = (int) $data->user_id;

    $user = Factory::getUser($userId);

    if (!$user || (int) $user->id !== $userId)
    {
        return;
    }

    $username = preg_replace('/\D/', '', (string) ($data->cpf ?? ''));
    ...
}
```
