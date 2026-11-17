#!/usr/bin/env bash
# Menu e launcher do DEVWORKS Harness. A configuracao fica no projeto atual.
set -euo pipefail
ROOT="$(pwd)"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG="$ROOT/config/harness.json"

usage() {
  cat <<'EOF'
Uso: scripts/harness.sh configure|run|resume [opcoes] [PHASES.md]

configure  escolhe modelos e limites para este projeto
run        inicia Ralph; use --engine nesta execucao quando necessario
resume     retoma Ralph; use --engine nesta execucao quando necessario
EOF
}

read_config() {
  python3 - "$CONFIG" <<'PY'
import json, sys
p=sys.argv[1]
try:
    d=json.load(open(p, encoding='utf8'))
except (OSError, ValueError): d={}
print(d.get('models',{}).get('implementation',''))
print(d.get('models',{}).get('verification',''))
print(d.get('limits',{}).get('implementation_minutes',30))
print(d.get('limits',{}).get('verification_minutes',5))
PY
}

configure() {
  mkdir -p "$ROOT/config"
  local implementation verification
  printf 'Modelo de implementacao (vazio = padrao da CLI): '
  read -r implementation
  printf 'Modelo de verificacao (vazio = padrao): '
  read -r verification
  HARNESS_IMPLEMENTATION_MODEL="$implementation" \
    HARNESS_VERIFICATION_MODEL="$verification" python3 - "$CONFIG" <<'PY'
import json, os, sys
path=sys.argv[1]
value={"models": {"implementation": os.environ["HARNESS_IMPLEMENTATION_MODEL"],
                  "verification": os.environ["HARNESS_VERIFICATION_MODEL"]},
       "limits": {"implementation_minutes": 30, "verification_minutes": 5,
                  "idle_warning_minutes": 5}}
with open(path, "w", encoding="utf8") as output:
    json.dump(value, output, ensure_ascii=False, indent=2)
    output.write("\n")
PY
  echo "Configuracao salva em config/harness.json"
}

launch() {
  local implementation="" verification="" implementation_limit=30 verification_limit=5 value index=0
  while IFS= read -r value; do
    case "$index" in
      0) implementation="$value" ;;
      1) verification="$value" ;;
      2) implementation_limit="$value" ;;
      3) verification_limit="$value" ;;
    esac
    index=$((index + 1))
  done < <(read_config)
  local args=()
  [ -n "$implementation" ] && export RALPH_IMPLEMENTATION_MODEL="$implementation"
  [ -n "$verification" ] && export RALPH_VERIFY_MODEL="$verification"
  export RALPH_IMPLEMENTATION_TIMEOUT=$((implementation_limit * 60))
  export RALPH_VERIFICATION_TIMEOUT=$((verification_limit * 60))
  local action="$1"; shift
  if [ "$action" = resume ]; then args+=(--from 1); fi
  exec "$SCRIPT_DIR/ralph.sh" "${args[@]}" "$@"
}

case "${1:-}" in
  configure) configure ;;
  run) shift; launch run "$@" ;;
  resume) shift; launch resume "$@" ;;
  *) usage; exit 2 ;;
esac
