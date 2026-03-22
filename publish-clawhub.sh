#!/bin/bash
# Publish all skills to ClawHub registry
# Usage: bash publish-clawhub.sh [--version VERSION]
#
# Prerequisites:
#   npm install -g clawhub
#   clawhub login  (opens browser for GitHub OAuth)
#
# Note: ClawHub rate-limits to 5 new skills per hour.
#       The script will pause and retry automatically.

set -e

VERSION="${1:-1.0.0}"

# Check auth
if ! clawhub whoami > /dev/null 2>&1; then
  echo "Error: Not logged in to ClawHub. Run: clawhub login"
  exit 1
fi

echo "Publishing skills to ClawHub (version $VERSION)..."

published=0
for skill_dir in skills/*/; do
  skill_name=$(basename "$skill_dir")

  if [ ! -f "$skill_dir/SKILL.md" ]; then
    echo "  SKIP $skill_name (no SKILL.md)"
    continue
  fi

  slug="acedatacloud-${skill_name}"
  echo "  Publishing $skill_name → $slug@$VERSION ..."

  # Retry with backoff on rate-limit errors
  attempts=0
  while true; do
    output=$(clawhub publish "$skill_dir" \
      --slug "$slug" \
      --version "$VERSION" \
      --changelog "Initial release" \
      --tags "latest,acedatacloud" 2>&1) && break

    if echo "$output" | grep -q "Rate limit"; then
      attempts=$((attempts + 1))
      wait_min=$((attempts * 15))
      echo "  Rate limited. Waiting ${wait_min}m before retrying $skill_name..."
      sleep $((wait_min * 60))
    else
      echo "  WARN: $skill_name failed: $output"
      break
    fi
  done

  published=$((published + 1))
  echo "  ✓ $slug ($published published)"
done

echo "Done! $published skills published."
echo "View at https://clawhub.ai/skills?q=acedatacloud"
