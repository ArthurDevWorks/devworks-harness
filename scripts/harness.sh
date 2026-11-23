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
m = d.get('models', {}) if isinstance(d.get('models'), dict) else {}
l = d.get('limits', {}) if isinstance(d.get('limits'), dict) else {}
print(m.get('implementation', ''))
print(m.get('verification', ''))
print(l.get('implementation_minutes', 30))
print(l.get('verification_minutes', 5))
print(','.join(str(x) for x in (m.get('priority_queue') or []) if x))
print(','.join(str(x) for x in (m.get('verify_queue') or []) if x))
PY
}

configure() {
  mkdir -p "$ROOT/config"
  local implementation verification priority_queue verify_queue
  printf 'Fila de prioridade engine:modelo separada por virgula (vazio = manter atual): '
  read -r priority_queue
  printf 'Fila de verificacao (vazio = seguir fila/padrao): '
  read -r verify_queue
  printf 'Modelo unitario de implementacao (vazio = padrao da CLI): '
  read -r implementation
  printf 'Modelo unitario de verificacao (vazio = padrao): '
  read -r verification
  HARNESS_IMPLEMENTATION_MODEL="$implementation" \
    HARNESS_VERIFICATION_MODEL="$verification" \
    HARNESS_PRIORITY_QUEUE="$priority_queue" \
    HARNESS_VERIFY_QUEUE="$verify_queue" python3 - "$CONFIG" <<'PY'
import json, os, sys
path = sys.argv[1]
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
    with open(path, "r", encoding="utf8") as f:
        existing = json.load(f)
    if not isinstance(existing, dict):
        existing = {}
except (OSError, ValueError):
    existing = {}

merged = dict(default)
merged["engines"] = existing.get("engines", []) if isinstance(existing.get("engines"), list) else []
models = dict(default["models"])
if isinstance(existing.get("models"), dict):
    models.update(existing["models"])
models["implementation"] = os.environ["HARNESS_IMPLEMENTATION_MODEL"]
models["verification"] = os.environ["HARNESS_VERIFICATION_MODEL"]
raw_pq = os.environ.get("HARNESS_PRIORITY_QUEUE", "").strip()
if raw_pq:
    models["priority_queue"] = [x.strip() for x in raw_pq.split(",") if x.strip()]
raw_vq = os.environ.get("HARNESS_VERIFY_QUEUE", "").strip()
if raw_vq:
    models["verify_queue"] = [x.strip() for x in raw_vq.split(",") if x.strip()]
merged["models"] = models

limits = dict(default["limits"])
if isinstance(existing.get("limits"), dict):
    limits.update(existing["limits"])
merged["limits"] = limits

with open(path, "w", encoding="utf8") as output:
    json.dump(merged, output, ensure_ascii=False, indent=2)
    output.write("\n")
PY
  echo "Configuracao salva em config/harness.json"
}

launch() {
  local implementation="" verification="" implementation_limit=30 verification_limit=5 priority_queue="" verify_queue="" value index=0
  while IFS= read -r value; do
    case "$index" in
      0) implementation="$value" ;;
      1) verification="$value" ;;
      2) implementation_limit="$value" ;;
      3) verification_limit="$value" ;;
      4) priority_queue="$value" ;;
      5) verify_queue="$value" ;;
    esac
    index=$((index + 1))
  done < <(read_config)
  local args=(--headless)
  [ -n "$priority_queue" ] && export RALPH_MODEL_QUEUE="$priority_queue"
  [ -n "$verify_queue" ] && export RALPH_VERIFY_QUEUE="$verify_queue"
  [ -z "$priority_queue" ] && [ -n "$implementation" ] && export RALPH_IMPLEMENTATION_MODEL="$implementation"
  [ -z "$verify_queue" ] && [ -n "$verification" ] && export RALPH_VERIFY_MODEL="$verification"
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
