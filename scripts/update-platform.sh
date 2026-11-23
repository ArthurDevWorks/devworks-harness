#!/usr/bin/env bash
# Atualiza uma instalacao de projeto a partir deste checkout canonico do Harness.

set -euo pipefail

PLATFORM=""
ROOT=""
CHECK_ONLY=false

usage() {
  cat <<'EOF'
Uso: scripts/update-platform.sh [--platform <engines>] [--root DIR] [--check]

Atualiza Skills e runtime de uma instalacao existente no projeto-alvo usando a
versao disponivel neste checkout do DEVWORKS Harness. Se --platform nao for
informado, usa as engines registradas em config/harness.json ou detecta pelos
Skills instalados.

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
    --platform|--engines)
      require_value "$1" "${2:-}"
      PLATFORM="${PLATFORM:+$PLATFORM,}$2"
      shift 2
      ;;
    --platform=*|--engines=*)
      PLATFORM="${PLATFORM:+$PLATFORM,}${1#*=}"
      shift
      ;;
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
  echo "Ignorando a engine legada em $ENGINE_FILE; as engines agora ficam em config/harness.json."
fi

has_skill_set() {
  local directory="$1"
  local skill
  for skill in init plan task-builder ai-context; do
    [ -s "$directory/$skill/SKILL.md" ] || return 1
  done
}

PYTHON_CMD=()
if command -v python3 >/dev/null 2>&1 && python3 -c '' </dev/null 2>/dev/null; then
  PYTHON_CMD=(python3)
elif [ -x /Library/Developer/CommandLineTools/usr/bin/python3 ] && arch -arm64 /Library/Developer/CommandLineTools/usr/bin/python3 -c '' </dev/null 2>/dev/null; then
  PYTHON_CMD=(arch -arm64 /Library/Developer/CommandLineTools/usr/bin/python3)
fi

if [ -z "$PLATFORM" ] && [ -f "$TARGET_ROOT/config/harness.json" ] && [ "${#PYTHON_CMD[@]}" -gt 0 ]; then
  PLATFORM=$("${PYTHON_CMD[@]}" - "$TARGET_ROOT/config/harness.json" <<'PY'
import json, sys
try:
    d = json.load(open(sys.argv[1], encoding="utf-8"))
    engines = d.get("engines") or []
    if isinstance(engines, list):
        print(",".join(str(e).strip() for e in engines if str(e).strip()))
except Exception:
    pass
PY
)
fi

if [ -z "$PLATFORM" ]; then
  detected=""
  if has_skill_set "$TARGET_ROOT/.claude/skills"; then
    detected="claude"
  fi
  if has_skill_set "$TARGET_ROOT/.opencode/skills"; then
    detected="${detected:+$detected,}opencode"
  fi
  if has_skill_set "$TARGET_ROOT/.agents/skills"; then
    echo "A instalacao em .agents/skills pode ser Codex ou Antigravity${detected:+ (alem de $detected)}." >&2
    echo "Informe --platform codex, --platform antigravity ou --platform codex,antigravity${detected:+,$detected}." >&2
    exit 1
  fi
  PLATFORM="$detected"
fi

if [ -z "$PLATFORM" ]; then
  echo "Nenhuma instalacao existente do DEVWORKS Harness foi encontrada em $TARGET_ROOT." >&2
  echo "Para a primeira instalacao, use scripts/install-platform.sh." >&2
  exit 1
fi

echo "Atualizando DEVWORKS Harness em $TARGET_ROOT (engines: $PLATFORM)"

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
