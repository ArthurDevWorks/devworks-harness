#!/usr/bin/env bash
# Adapter Ralph: Antigravity CLI.

engine_binary() { printf '%s' 'agy'; }
engine_install_hint() { printf '%s' 'https://antigravity.google/docs/cli/install/'; }
adapter_usage_pattern() { printf '%s' 'resource_exhausted|rate limit reached|quota exceeded|usage limit reached|too many requests|[[:space:]]429[[:space:]]'; }

adapter_run_engine_once() {
  local prompt_file="$1" log_file="$2" mode="$3" rc=0 quiet=0
  if [[ "$mode" == "verify" ]]; then
    agy -p "$(cat "$prompt_file")" --mode plan --sandbox --output-format text \
      --print-timeout "$ANTIGRAVITY_TIMEOUT" "${ENGINE_MODEL_ARGS[@]}" 2>&1 | tee "$log_file" || rc=$?
  else
    $DASHBOARD && quiet=1
    if agy -p "$(cat "$prompt_file")" --mode accept-edits --output-format stream-json \
         "${ENGINE_MODEL_ARGS[@]}" \
         --print-timeout "$ANTIGRAVITY_TIMEOUT" --dangerously-skip-permissions 2>&1 | tee "$log_file" \
         | stream_watch "$LIVE_STATE" "${RALPH_PHASE_NUM:-0}" "$quiet" "$CURRENT_PHASE_FILE"; then rc=0; else rc=$?; fi
  fi
  return "$rc"
}

adapter_gate0_validate() {
  local log_file="$1" result
  result=$(grep -E '"event"[[:space:]]*:[[:space:]]*"result"' "$log_file" | tail -n 1)
  if [ -z "$result" ]; then GATE_CAUSE="Antigravity terminou sem publicar o evento result."; return 1; fi
  if ! grep -qE '"status"[[:space:]]*:[[:space:]]*"SUCCESS"' <<< "$result"; then GATE_CAUSE="Antigravity terminou com status diferente de SUCCESS."; return 1; fi
  return 0
}
