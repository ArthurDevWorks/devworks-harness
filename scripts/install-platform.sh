#!/usr/bin/env bash
# Instala os workflows canônicos e, no escopo de projeto, o runtime local do
# Harness para que o projeto não dependa do caminho do repositório central.

set -euo pipefail

PLATFORM=""
SCOPE="project"
ROOT=""

usage() {
  cat <<'EOF'
Uso: scripts/install-platform.sh --platform codex|claude|opencode|antigravity [--scope project|user] [--root DIR] [--check]

Instala os Skills canônicos init, plan, task-builder e ai-context. No escopo
project, instala também scripts/ralph.sh, scripts/ralph-web.sh,
scripts/ralph-watch.sh, adapters, dashboard e configuração no projeto-alvo.
O plugin Claude e seus comandos existentes permanecem compatíveis.
EOF
}

CHECK_ONLY=false
while [[ $# -gt 0 ]]; do
  case "$1" in
    --platform) PLATFORM="$2"; shift 2 ;;
    --platform=*) PLATFORM="${1#*=}"; shift ;;
    --scope) SCOPE="$2"; shift 2 ;;
    --scope=*) SCOPE="${1#*=}"; shift ;;
    --root) ROOT="$2"; shift 2 ;;
    --root=*) ROOT="${1#*=}"; shift ;;
    --check) CHECK_ONLY=true; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Opcao desconhecida: $1" >&2; usage >&2; exit 2 ;;
  esac
done

case "$PLATFORM" in codex|claude|opencode|antigravity) ;; *) usage >&2; exit 2 ;; esac
case "$SCOPE" in project|user) ;; *) echo "Escopo invalido: $SCOPE" >&2; exit 2 ;; esac

BIN="$PLATFORM"
[ "$PLATFORM" = "antigravity" ] && BIN="agy"
if ! command -v "$BIN" >/dev/null 2>&1; then
  echo "CLI '$BIN' nao encontrada. Instale-a e autentique antes de executar o Ralph." >&2
  exit 1
fi
VERSION="$($BIN --version 2>/dev/null | head -n 1 || true)"
if [ -z "$VERSION" ]; then
  echo "Nao foi possivel validar a versao de '$BIN'." >&2
  exit 1
fi
echo "CLI: $BIN ($VERSION)"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_DIR="$SCRIPT_DIR/../skills"
HARNESS_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

missing_skills=()
for skill in init plan task-builder ai-context; do
  [ -s "$SKILLS_DIR/$skill/SKILL.md" ] || missing_skills+=("$skill")
done
if [ "${#missing_skills[@]}" -gt 0 ]; then
  echo "Skills canônicos ausentes: ${missing_skills[*]}." >&2
  exit 1
fi

if [ -n "$ROOT" ]; then
  TARGET_ROOT="$(cd "$ROOT" && pwd)"
elif [ "$SCOPE" = "project" ]; then
  TARGET_ROOT="$(pwd)"
else
  TARGET_ROOT="${HOME}"
fi

case "$PLATFORM:$SCOPE" in
  codex:project) DEST="$TARGET_ROOT/.agents/skills" ;;
  codex:user) DEST="$TARGET_ROOT/.codex/skills" ;;
  claude:project) DEST="$TARGET_ROOT/.claude/skills" ;;
  claude:user) DEST="$TARGET_ROOT/.claude/skills" ;;
  opencode:project) DEST="$TARGET_ROOT/.opencode/skills" ;;
  opencode:user) DEST="$TARGET_ROOT/.config/opencode/skills" ;;
  antigravity:project) DEST="$TARGET_ROOT/.agents/skills" ;;
  antigravity:user) DEST="$TARGET_ROOT/.gemini/config/skills" ;;
esac

if [ "$CHECK_ONLY" = true ]; then
  echo "Destino validado: $DEST"
  if [ "$SCOPE" = "project" ]; then
    echo "Runtime validado: $TARGET_ROOT/scripts e $TARGET_ROOT/config"
  fi
  exit 0
fi

mkdir -p "$DEST"
for skill in init plan task-builder ai-context; do
  mkdir -p "$DEST/$skill"
  cp -R "$SKILLS_DIR/$skill/." "$DEST/$skill/"
done

echo "Skills instalados em $DEST"
if [ "$SCOPE" = "project" ]; then
  mkdir -p "$TARGET_ROOT/scripts/engines" "$TARGET_ROOT/scripts/dashboard/web" "$TARGET_ROOT/config"
  cp "$HARNESS_ROOT/scripts/ralph.sh" "$TARGET_ROOT/scripts/ralph.sh"
  cp "$HARNESS_ROOT/scripts/ralph-web.sh" "$TARGET_ROOT/scripts/ralph-web.sh"
  cp "$HARNESS_ROOT/scripts/ralph-watch.sh" "$TARGET_ROOT/scripts/ralph-watch.sh"
  cp "$HARNESS_ROOT/scripts/engines/"*.sh "$TARGET_ROOT/scripts/engines/"
  cp "$HARNESS_ROOT/scripts/dashboard/server.py" "$TARGET_ROOT/scripts/dashboard/server.py"
  cp "$HARNESS_ROOT/scripts/dashboard/web/"* "$TARGET_ROOT/scripts/dashboard/web/"
  cp "$HARNESS_ROOT/config/model-policy.tsv" "$TARGET_ROOT/config/model-policy.tsv"
  printf '%s\n' "$PLATFORM" > "$TARGET_ROOT/config/devworks-harness-engine"
  chmod +x "$TARGET_ROOT/scripts/ralph.sh" "$TARGET_ROOT/scripts/ralph-web.sh" \
    "$TARGET_ROOT/scripts/ralph-watch.sh" "$TARGET_ROOT/scripts/engines/"*.sh
  echo "Runtime instalado em $TARGET_ROOT/scripts"
  echo "Engine padrao registrada: $PLATFORM"
fi
if [ "$PLATFORM" = "claude" ]; then
  echo "Claude Code: os comandos legados do plugin continuam preservados."
fi
echo "Use init, plan, task-builder ou ai-context conforme a interface da plataforma."
