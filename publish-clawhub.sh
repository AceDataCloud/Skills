#!/bin/bash
# Update one existing ClawHub listing. Preview is the default.
set -euo pipefail
repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$repo_dir/scripts/publish_clawhub.py" "$@"
