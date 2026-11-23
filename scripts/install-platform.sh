#!/usr/bin/env bash
# Instala os workflows canônicos e, no escopo de projeto, o runtime local do
# Harness para que o projeto não dependa do caminho do repositório central.

set -euo pipefail

PLATFORMS_RAW=()
SCOPE="project"
ROOT=""
CHECK_ONLY=false

usage() {
  cat <<'EOF'
Uso: scripts/install-platform.sh --platform <engines> [--scope project|user] [--root DIR] [--check]

  --platform, --engines  codex, claude, opencode, antigravity, lista separada
                         por virgula (ex: codex,antigravity), flag repetida
                         ou 'all' (todas as CLIs instaladas).
  --scope                project (padrao) ou user
  --root DIR             diretorio do projeto-alvo (padrao: diretorio atual)
  --check                valida CLIs e destinos sem alterar arquivos

Instala os Skills canônicos init, plan, task-builder e ai-context. No escopo
project, instala também scripts/ralph.sh, scripts/ralph-web.sh,
scripts/ralph-watch.sh, adapters, dashboard e configuração (incluindo as
engines habilitadas em config/harness.json) no projeto-alvo.
EOF
}

require_value() {
  local option="$1" value="${2:-}"
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
      PLATFORMS_RAW+=("$2")
      shift 2
      ;;
    --platform=*|--engines=*)
      PLATFORMS_RAW+=("${1#*=}")
      shift
      ;;
    --scope)
      require_value "$1" "${2:-}"
      SCOPE="$2"
      shift 2
      ;;
    --scope=*) SCOPE="${1#*=}"; shift ;;
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

if [ "${#PLATFORMS_RAW[@]}" -eq 0 ]; then
  usage >&2
  exit 2
fi

case "$SCOPE" in project|user) ;; *) echo "Escopo invalido: $SCOPE" >&2; exit 2 ;; esac

engine_bin_for() {
  case "$1" in
    antigravity) printf '%s' 'agy' ;;
    *) printf '%s' "$1" ;;
  esac
}

PLATFORMS=()
add_platform() {
  local p="$1" existing
  case "$p" in
    codex|claude|opencode|antigravity) ;;
    *) echo "Plataforma invalida: $p" >&2; usage >&2; exit 2 ;;
  esac
  for existing in "${PLATFORMS[@]+"${PLATFORMS[@]}"}"; do
    [ "$existing" = "$p" ] && return 0
  done
  PLATFORMS+=("$p")
}

HAS_ALL=false
for raw in "${PLATFORMS_RAW[@]}"; do
  IFS=',' read -r -a parts <<< "$raw"
  for part in "${parts[@]}"; do
    part="${part//[[:space:]]/}"
    [ -n "$part" ] || continue
    if [ "$part" = "all" ]; then
      HAS_ALL=true
    else
      add_platform "$part"
    fi
  done
done

if [ "$HAS_ALL" = true ]; then
  for candidate in codex claude opencode antigravity; do
    bin=$(engine_bin_for "$candidate")
    if command -v "$bin" >/dev/null 2>&1; then
      add_platform "$candidate"
    fi
  done
  if [ "${#PLATFORMS[@]}" -eq 0 ]; then
    echo "Nenhuma CLI de engine (codex, claude, opencode, agy) encontrada no PATH." >&2
    exit 1
  fi
fi

if [ "${#PLATFORMS[@]}" -eq 0 ]; then
  usage >&2
  exit 2
fi

for platform in "${PLATFORMS[@]}"; do
  BIN=$(engine_bin_for "$platform")
  if ! command -v "$BIN" >/dev/null 2>&1; then
    echo "CLI '$BIN' nao encontrada para '$platform'. Instale-a e autentique antes de executar o Ralph." >&2
    exit 1
  fi
  VERSION="$($BIN --version 2>/dev/null | head -n 1 || true)"
  if [ -z "$VERSION" ]; then
    echo "Nao foi possivel validar a versao de '$BIN'." >&2
    exit 1
  fi
  echo "CLI [$platform]: $BIN ($VERSION)"
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
SKILLS_DIR="$SCRIPT_DIR/../skills"
HARNESS_ROOT="$(cd "$SCRIPT_DIR/.." && pwd -P)"

missing_skills=()
for skill in init plan task-builder ai-context; do
  [ -s "$SKILLS_DIR/$skill/SKILL.md" ] || missing_skills+=("$skill")
done
if [ "${#missing_skills[@]}" -gt 0 ]; then
  echo "Skills canônicos ausentes: ${missing_skills[*]}." >&2
  exit 1
fi

if [ -n "$ROOT" ]; then
  TARGET_ROOT="$(cd "$ROOT" && pwd -P)"
elif [ "$SCOPE" = "project" ]; then
  TARGET_ROOT="$(pwd -P)"
else
  TARGET_ROOT="${HOME}"
fi

dest_for() {
  case "$1:$SCOPE" in
    codex:project) printf '%s' "$TARGET_ROOT/.agents/skills" ;;
    codex:user) printf '%s' "$TARGET_ROOT/.codex/skills" ;;
    claude:project) printf '%s' "$TARGET_ROOT/.claude/skills" ;;
    claude:user) printf '%s' "$TARGET_ROOT/.claude/skills" ;;
    opencode:project) printf '%s' "$TARGET_ROOT/.opencode/skills" ;;
    opencode:user) printf '%s' "$TARGET_ROOT/.config/opencode/skills" ;;
    antigravity:project) printf '%s' "$TARGET_ROOT/.agents/skills" ;;
    antigravity:user) printf '%s' "$TARGET_ROOT/.gemini/config/skills" ;;
  esac
}

DESTS=()
add_dest() {
  local d="$1" existing
  for existing in "${DESTS[@]+"${DESTS[@]}"}"; do
    [ "$existing" = "$d" ] && return 0
  done
  DESTS+=("$d")
}

for platform in "${PLATFORMS[@]}"; do
  add_dest "$(dest_for "$platform")"
done

if [ "$CHECK_ONLY" = true ]; then
  for dest in "${DESTS[@]}"; do
    echo "Destino validado: $dest"
  done
  if [ "$SCOPE" = "project" ]; then
    echo "Runtime validado: $TARGET_ROOT/scripts e $TARGET_ROOT/config"
    echo "Engines configuradas: ${PLATFORMS[*]}"
  fi
  exit 0
fi

for dest in "${DESTS[@]}"; do
  mkdir -p "$dest"
  for skill in init plan task-builder ai-context; do
    mkdir -p "$dest/$skill"
    cp -R "$SKILLS_DIR/$skill/." "$dest/$skill/"
  done
  echo "Skills instalados em $dest"
done

if [ "$SCOPE" = "project" ]; then
  mkdir -p "$TARGET_ROOT/scripts/engines" "$TARGET_ROOT/scripts/dashboard/web" "$TARGET_ROOT/config"
  if [ "$HARNESS_ROOT" != "$TARGET_ROOT" ]; then
    cp "$HARNESS_ROOT/scripts/ralph.sh" "$TARGET_ROOT/scripts/ralph.sh"
    cp "$HARNESS_ROOT/scripts/harness.sh" "$TARGET_ROOT/scripts/harness.sh"
    cp "$HARNESS_ROOT/scripts/ralph-web.sh" "$TARGET_ROOT/scripts/ralph-web.sh"
    cp "$HARNESS_ROOT/scripts/ralph-watch.sh" "$TARGET_ROOT/scripts/ralph-watch.sh"
    cp "$HARNESS_ROOT/scripts/engines/"*.sh "$TARGET_ROOT/scripts/engines/"
    cp "$HARNESS_ROOT/scripts/dashboard/server.py" "$TARGET_ROOT/scripts/dashboard/server.py"
    cp "$HARNESS_ROOT/scripts/dashboard/web/"* "$TARGET_ROOT/scripts/dashboard/web/"
    cp "$HARNESS_ROOT/config/model-policy.tsv" "$TARGET_ROOT/config/model-policy.tsv"
    if [ ! -f "$TARGET_ROOT/config/harness.json" ]; then
      cp "$HARNESS_ROOT/config/harness.json" "$TARGET_ROOT/config/harness.json"
    fi
    if [ -f "$HARNESS_ROOT/config/coding-style-profile.md" ]; then
      cp "$HARNESS_ROOT/config/coding-style-profile.md" "$TARGET_ROOT/config/coding-style-profile.md"
    fi
  fi

  ENGINES_CSV=$(IFS=','; printf '%s' "${PLATFORMS[*]}")
  PYTHON_CMD=()
  if command -v python3 >/dev/null 2>&1 && python3 -c '' </dev/null 2>/dev/null; then
    PYTHON_CMD=(python3)
  elif [ -x /Library/Developer/CommandLineTools/usr/bin/python3 ] && arch -arm64 /Library/Developer/CommandLineTools/usr/bin/python3 -c '' </dev/null 2>/dev/null; then
    PYTHON_CMD=(arch -arm64 /Library/Developer/CommandLineTools/usr/bin/python3)
  fi
  if [ "${#PYTHON_CMD[@]}" -gt 0 ]; then
    HARNESS_ENGINES="$ENGINES_CSV" "${PYTHON_CMD[@]}" - "$TARGET_ROOT/config/harness.json" <<'PY'
import json, os, sys

path = sys.argv[1]
engines = [e for e in os.environ.get("HARNESS_ENGINES", "").split(",") if e]
default = {
    "engines": [],
    "models": {
        "implementation": "",
        "verification": "",
        "priority_queue": [],
        "verify_queue": [],
    },
    "limits": {
        "implementation_minutes": 30,
        "verification_minutes": 5,
        "idle_warning_minutes": 5,
    },
}
try:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        data = {}
except (OSError, ValueError):
    data = {}

merged = dict(default)
merged.update(data)
models = dict(default["models"])
if isinstance(data.get("models"), dict):
    models.update(data["models"])
merged["models"] = models
limits = dict(default["limits"])
if isinstance(data.get("limits"), dict):
    limits.update(data["limits"])
merged["limits"] = limits
merged["engines"] = engines

with open(path, "w", encoding="utf-8") as f:
    json.dump(merged, f, ensure_ascii=False, indent=2)
    f.write("\n")
PY
  fi

  chmod +x "$TARGET_ROOT/scripts/ralph.sh" "$TARGET_ROOT/scripts/harness.sh" "$TARGET_ROOT/scripts/ralph-web.sh" \
    "$TARGET_ROOT/scripts/ralph-watch.sh" "$TARGET_ROOT/scripts/engines/"*.sh
  echo "Runtime instalado em $TARGET_ROOT/scripts"
  echo "Engines registradas em config/harness.json: ${PLATFORMS[*]}"
fi

for platform in "${PLATFORMS[@]}"; do
  if [ "$platform" = "claude" ]; then
    echo "Claude Code: os comandos legados do plugin continuam preservados."
  fi
done
echo "Use init, plan, task-builder ou ai-context conforme a interface da plataforma."
