#!/usr/bin/env bash
# Adapter Ralph: OpenCode.

engine_binary() { printf '%s' 'opencode'; }
engine_install_hint() { printf '%s' 'https://opencode.ai/docs'; }
adapter_usage_pattern() { printf '%s' 'rate limit reached|quota exceeded|usage limit reached|too many requests|resource_exhausted'; }

adapter_run_engine_once() {
  local prompt_file="$1" log_file="$2" mode="$3" rc=0 quiet=0
  if [[ "$mode" == "verify" ]]; then
    OPENCODE_CONFIG_CONTENT='{"permission":{"*":"deny","read":"allow","glob":"allow","grep":"allow"}}' \
      opencode run --format default "${ENGINE_MODEL_ARGS[@]}" < "$prompt_file" 2>&1 | tee "$log_file" || rc=$?
  else
    $DASHBOARD && quiet=1
    if opencode run --auto --format json < "$prompt_file" 2>&1 | tee "$log_file" \
         | stream_watch "$LIVE_STATE" "${RALPH_PHASE_NUM:-0}" "$quiet" "$CURRENT_PHASE_FILE"; then rc=0; else rc=$?; fi
  fi
  return "$rc"
}

adapter_gate0_validate() {
  local log_file="$1"
  if grep -qE '^\{.*"type"[[:space:]]*:[[:space:]]*"error"' "$log_file"; then GATE_CAUSE="OpenCode publicou um evento de erro."; return 1; fi
  if ! grep -qE '^\{.*"type"[[:space:]]*:[[:space:]]*"step_finish"' "$log_file"; then GATE_CAUSE="OpenCode terminou sem publicar o evento step_finish."; return 1; fi
  return 0
}
