#!/usr/bin/env bash
#
# ralph-web.sh — painel web local para configurar e acompanhar o Ralph.

set -euo pipefail

REPO="."
PORT="7331"
OPEN_BROWSER=true
PREFILL_INPUT=""

usage() {
  cat <<'EOF'
Uso: scripts/ralph-web.sh [--port PORTA] [--input CAMINHO] [--no-open] [caminho-do-repositorio]

Inicia o painel Ralph em http://127.0.0.1:<porta> e abre automaticamente no
navegador (a menos que --no-open ou RALPH_NO_OPEN=1 seja usado). O servidor é
local e permite escolher engines/modelos, selecionar fases, iniciar, acompanhar
e encerrar execuções.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --port) PORT="$2"; shift 2 ;;
    --port=*) PORT="${1#*=}"; shift ;;
    --input) PREFILL_INPUT="$2"; shift 2 ;;
    --input=*) PREFILL_INPUT="${1#*=}"; shift ;;
    --no-open) OPEN_BROWSER=false; shift ;;
    -h|--help)
      usage
      exit 0
      ;;
    *) REPO="$1"; shift ;;
  esac
done

if [ "${RALPH_NO_OPEN:-0}" = "1" ]; then
  OPEN_BROWSER=false
fi

if ! [[ "$PORT" =~ ^[0-9]+$ ]] || [ "$PORT" -lt 1 ] || [ "$PORT" -gt 65535 ]; then
  echo "Porta invalida: $PORT" >&2
  exit 1
fi

PYTHON_BIN="${RALPH_PYTHON:-}"
PYTHON_ARCH=()
if [ -z "$PYTHON_BIN" ]; then
  APPLE_SILICON=false
  if [ "$(uname -s)" = "Darwin" ]; then
    [ "$(uname -m)" = "arm64" ] && APPLE_SILICON=true
    [ "$(/usr/sbin/sysctl -n hw.optional.arm64 2>/dev/null || true)" = "1" ] && APPLE_SILICON=true
  fi
  if $APPLE_SILICON && [ -x /Library/Developer/CommandLineTools/usr/bin/python3 ]; then
    PYTHON_BIN=/Library/Developer/CommandLineTools/usr/bin/python3
    PYTHON_ARCH=(arch -arm64)
  elif command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python3)"
  fi
fi
if [ -z "$PYTHON_BIN" ] || [ ! -x "$PYTHON_BIN" ]; then
  echo "python3 e necessario para o monitor web." >&2
  exit 1
fi

REPO="$(cd "$REPO" && pwd)"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

URL="http://127.0.0.1:${PORT}"
if [ -n "$PREFILL_INPUT" ]; then
  ENCODED_INPUT=$("${PYTHON_ARCH[@]}" "$PYTHON_BIN" -c 'import sys, urllib.parse; print(urllib.parse.quote(sys.argv[1]))' "$PREFILL_INPUT")
  URL="${URL}/?input=${ENCODED_INPUT}"
fi

open_browser_when_ready() {
  local target_url="$1" port="$2" opener=""
  if command -v open >/dev/null 2>&1; then
    opener="open"
  elif command -v xdg-open >/dev/null 2>&1; then
    opener="xdg-open"
  else
    return 0
  fi

  (
    local i=0
    while [ "$i" -lt 40 ]; do
      if "${PYTHON_ARCH[@]}" "$PYTHON_BIN" -c "import socket, sys; s=socket.socket(); s.settimeout(0.2); rc=s.connect_ex(('127.0.0.1', int(sys.argv[1]))); s.close(); sys.exit(0 if rc==0 else 1)" "$port" 2>/dev/null; then
        "$opener" "$target_url" >/dev/null 2>&1 || true
        exit 0
      fi
      sleep 0.15
      i=$((i + 1))
    done
  ) &
}

echo "Ralph Web: ${URL}"
echo "Painel local Ralph. Ctrl-C para encerrar o painel."
if [ "$OPEN_BROWSER" = true ]; then
  open_browser_when_ready "$URL" "$PORT"
fi
exec "${PYTHON_ARCH[@]}" "$PYTHON_BIN" "$SCRIPT_DIR/dashboard/server.py" --repo "$REPO" --port "$PORT"
