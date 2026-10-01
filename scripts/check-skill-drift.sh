#!/usr/bin/env bash
# Garante que os adaptadores de host apontam para os mesmos Skills canônicos.

set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FAIL=0

for skill in init plan task-builder ai-context; do
  file="$ROOT/skills/$skill/SKILL.md"
  if [ ! -s "$file" ]; then
    echo "ERRO: skill canônico ausente: $file" >&2
    FAIL=1
    continue
  fi
  if ! grep -q "^name: $skill$" "$file" || ! grep -q '^description:' "$file"; then
    echo "ERRO: frontmatter inválido: $file" >&2
    FAIL=1
  fi
done

for platform in codex claude opencode antigravity; do
  adapter="$ROOT/docs/agents/$platform.md"
  if [ ! -s "$adapter" ]; then
    echo "ERRO: adaptador de host ausente: $adapter" >&2
    FAIL=1
    continue
  fi
  for skill in init plan task-builder ai-context; do
    if ! grep -q "skills/$skill" "$adapter"; then
      echo "ERRO: $adapter não referencia skills/$skill" >&2
      FAIL=1
    fi
  done
done

[ "$FAIL" -eq 0 ] && echo "OK: Skills e adaptadores sem drift."
exit "$FAIL"
