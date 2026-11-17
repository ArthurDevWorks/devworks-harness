#!/usr/bin/env bash
# Adapter Ralph: Codex CLI.

engine_binary() { printf '%s' 'codex'; }
engine_install_hint() { printf '%s' 'npm install -g @openai/codex'; }
adapter_usage_pattern() { printf '%s' 'rate limit reached|quota exceeded|usage limit reached|too many requests|resource_exhausted'; }

adapter_run_engine_once() {
  local prompt_file="$1" log_file="$2" mode="$3" rc=0
  local -a limiter=()
  if [ "${RALPH_SESSION_TIMEOUT_SECONDS:-0}" -gt 0 ] && command -v timeout >/dev/null 2>&1; then limiter=(timeout "$RALPH_SESSION_TIMEOUT_SECONDS"); fi
  if [[ "$mode" == "verify" ]]; then
    "${limiter[@]}" codex exec --sandbox read-only "${ENGINE_MODEL_ARGS[@]}" - < "$prompt_file" 2>&1 | tee "$log_file" || rc=$?
  else
    "${limiter[@]}" codex exec --sandbox danger-full-access "${ENGINE_MODEL_ARGS[@]}" - < "$prompt_file" 2>&1 | tee "$log_file" || rc=$?
  fi
  return "$rc"
}

adapter_gate0_validate() { return 0; }
