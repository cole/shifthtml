#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

failed=0
for dir in */; do
    [[ -f "$dir/pyproject.toml" ]] || continue
    echo "=== ${dir%/} ==="
    if uv run --directory "$dir" pytest -q "$@"; then
        echo
    else
        failed=1
        echo
    fi
done

exit $failed
