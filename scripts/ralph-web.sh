#!/usr/bin/env bash
#
# ralph-web.sh — monitor web local, somente leitura, para o Ralph.

set -euo pipefail

REPO="."
PORT="7331"

usage() {
  cat <<'EOF'
Uso: scripts/ralph-web.sh [--port PORTA] [caminho-do-repositorio]

Inicia o monitor Ralph em http://127.0.0.1:<porta>. O servidor é local,
somente leitura e não controla execuções.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --port) PORT="$2"; shift 2 ;;
    --port=*) PORT="${1#*=}"; shift ;;
    -h|--help)
      usage
      exit 0
      ;;
    *) REPO="$1"; shift ;;
  esac
done

if ! [[ "$PORT" =~ ^[0-9]+$ ]] || [ "$PORT" -lt 1 ] || [ "$PORT" -gt 65535 ]; then
  echo "Porta invalida: $PORT" >&2
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 e necessario para o monitor web." >&2
  exit 1
fi

REPO="$(cd "$REPO" && pwd)"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Ralph Web: http://127.0.0.1:${PORT}"
echo "Monitor local e somente leitura. Ctrl-C para encerrar."
exec python3 "$SCRIPT_DIR/dashboard/server.py" --repo "$REPO" --port "$PORT"
