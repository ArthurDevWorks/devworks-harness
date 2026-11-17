#!/usr/bin/env bash
# Atualiza uma instalacao de projeto a partir deste checkout canonico do Harness.

set -euo pipefail

PLATFORM=""
ROOT=""
CHECK_ONLY=false

usage() {
  cat <<'EOF'
Uso: scripts/update-platform.sh [--platform codex|claude|opencode|antigravity] [--root DIR] [--check]

Atualiza Skills e runtime de uma instalacao existente no projeto-alvo usando a
versao disponivel neste checkout do DEVWORKS Harness. A plataforma e detectada
pelos Skills instalados; se houver mais de uma, informe --platform.

O script nao atualiza este repositorio com git pull e nao altera artefatos de
trabalho do projeto, como .spec/, PHASES.md e .phases/.
EOF
}

require_value() {
  local option="$1"
  local value="${2:-}"
  if [ -z "$value" ] || [[ "$value" = --* ]]; then
    echo "Valor ausente para $option." >&2
    usage >&2
    exit 2
  fi
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --platform)
      require_value "$1" "${2:-}"
      PLATFORM="$2"
      shift 2
      ;;
    --platform=*) PLATFORM="${1#*=}"; shift ;;
    --root)
      require_value "$1" "${2:-}"
      ROOT="$2"
      shift 2
      ;;
    --root=*) ROOT="${1#*=}"; shift ;;
    --check) CHECK_ONLY=true; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Opcao desconhecida: $1" >&2; usage >&2; exit 2 ;;
  esac
done

case "$PLATFORM" in
  ""|codex|claude|opencode|antigravity) ;;
  *) echo "Plataforma invalida: $PLATFORM" >&2; usage >&2; exit 2 ;;
esac

if [ -n "$ROOT" ]; then
  if [ ! -d "$ROOT" ]; then
    echo "Projeto-alvo inexistente: $ROOT" >&2
    exit 1
  fi
  TARGET_ROOT="$(cd "$ROOT" && pwd)"
else
  TARGET_ROOT="$(pwd)"
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALLER="$SCRIPT_DIR/install-platform.sh"
if [ ! -x "$INSTALLER" ]; then
  echo "Instalador canonico nao executavel: $INSTALLER" >&2
  exit 1
fi

ENGINE_FILE="$TARGET_ROOT/config/devworks-harness-engine"
if [ -f "$ENGINE_FILE" ]; then
  echo "Ignorando a engine legada em $ENGINE_FILE; a engine agora é escolhida por execução."
fi

has_skill_set() {
  local directory="$1"
  local skill
  for skill in init plan task-builder ai-context; do
    [ -s "$directory/$skill/SKILL.md" ] || return 1
  done
}

if [ -z "$PLATFORM" ]; then
  detected=""
  if has_skill_set "$TARGET_ROOT/.claude/skills"; then
    detected="claude"
  fi
  if has_skill_set "$TARGET_ROOT/.opencode/skills"; then
    if [ -n "$detected" ]; then
      echo "Mais de uma instalacao de engine foi encontrada. Informe --platform." >&2
      exit 1
    fi
    detected="opencode"
  fi
  if has_skill_set "$TARGET_ROOT/.agents/skills"; then
    echo "A instalacao antiga em .agents/skills pode ser Codex ou Antigravity." >&2
    echo "Informe --platform codex ou --platform antigravity." >&2
    exit 1
  fi
  PLATFORM="$detected"
fi

if [ -z "$PLATFORM" ]; then
  echo "Nenhuma instalacao existente do DEVWORKS Harness foi encontrada em $TARGET_ROOT." >&2
  echo "Para a primeira instalacao, use scripts/install-platform.sh." >&2
  exit 1
fi

case "$PLATFORM" in
  codex|antigravity) SKILLS_DEST="$TARGET_ROOT/.agents/skills" ;;
  claude) SKILLS_DEST="$TARGET_ROOT/.claude/skills" ;;
  opencode) SKILLS_DEST="$TARGET_ROOT/.opencode/skills" ;;
esac

if ! has_skill_set "$SKILLS_DEST" && [ ! -x "$TARGET_ROOT/scripts/ralph.sh" ]; then
  echo "A engine foi identificada, mas a instalacao do Harness nao foi encontrada em $TARGET_ROOT." >&2
  echo "Para a primeira instalacao, use scripts/install-platform.sh." >&2
  exit 1
fi

echo "Atualizando DEVWORKS Harness em $TARGET_ROOT (engine: $PLATFORM)"

INSTALL_ARGS=(--platform "$PLATFORM" --scope project --root "$TARGET_ROOT")
if [ "$CHECK_ONLY" = true ]; then
  INSTALL_ARGS+=(--check)
fi
"$INSTALLER" "${INSTALL_ARGS[@]}"

if [ "$CHECK_ONLY" = true ]; then
  echo "Atualizacao validada; nenhum arquivo foi alterado."
else
  echo "Atualizacao concluida com a versao disponivel em $(cd "$SCRIPT_DIR/.." && pwd)."
fi
