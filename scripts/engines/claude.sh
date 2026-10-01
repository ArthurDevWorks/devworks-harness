#!/usr/bin/env bash
# Adapter Ralph: Claude Code.

engine_binary() { printf '%s' 'claude'; }
engine_install_hint() { printf '%s' 'npm install -g @anthropic-ai/claude-code'; }
adapter_usage_pattern() { printf '%s' 'usage limit reached|hit your (session|usage|[0-9]+-hour) limit|[0-9]+-hour limit reached|"api_error_status"[[:space:]]*:[[:space:]]*429'; }

adapter_run_engine_once() {
  local prompt_file="$1" log_file="$2" mode="$3" rc=0 quiet=0
  if [[ "$mode" == "verify" ]]; then
    env -u CLAUDECODE claude --dangerously-skip-permissions "${ENGINE_MODEL_ARGS[@]}" \
      -p "$(cat "$prompt_file")" --allowedTools "Read,Glob,Grep" --output-format text \
      < /dev/null 2>&1 | tee "$log_file" || rc=$?
  else
    $DASHBOARD && quiet=1
    if env -u CLAUDECODE claude --dangerously-skip-permissions -p "$(cat "$prompt_file")" \
         --output-format stream-json --verbose < /dev/null 2>&1 | tee "$log_file" \
         | stream_watch "$LIVE_STATE" "${RALPH_PHASE_NUM:-0}" "$quiet" "$CURRENT_PHASE_FILE"; then rc=0; else rc=$?; fi
  fi
  return "$rc"
}

adapter_gate0_validate() {
  local log_file="$1" result_line
  result_line=$(grep -F '"type":"result"' "$log_file" | tail -n 1)
  [ -z "$result_line" ] && result_line=$(grep -F '"type": "result"' "$log_file" | tail -n 1)
  if [ -z "$result_line" ]; then GATE_CAUSE="O engine terminou sem emitir um resultado."; return 1; fi
  if grep -qE '"is_error"[[:space:]]*:[[:space:]]*true' <<< "$result_line"; then GATE_CAUSE="O engine reportou is_error=true no resultado."; return 1; fi
  return 0
}
