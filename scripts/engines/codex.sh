#!/usr/bin/env bash
# Adapter Ralph: Codex CLI.

engine_binary() { printf '%s' 'codex'; }
engine_install_hint() { printf '%s' 'npm install -g @openai/codex'; }
adapter_usage_pattern() { printf '%s' 'rate limit reached|quota exceeded|usage limit reached|too many requests|resource_exhausted'; }

adapter_run_engine_once() {
  local prompt_file="$1" log_file="$2" mode="$3" rc=0
  if [[ "$mode" == "verify" ]]; then
    codex exec --sandbox read-only "${ENGINE_MODEL_ARGS[@]}" - < "$prompt_file" 2>&1 | tee "$log_file" || rc=$?
  else
    codex exec --sandbox danger-full-access - < "$prompt_file" 2>&1 | tee "$log_file" || rc=$?
  fi
  return "$rc"
}

adapter_gate0_validate() { return 0; }
