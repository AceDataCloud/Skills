#!/bin/bash
# Publish all skills to ClawHub registry
# Usage: ./publish-clawhub.sh
#
# Prerequisites:
#   npm install -g clawhub
#   clawhub login  (opens browser for GitHub OAuth)

set -e

# Check auth
if ! clawhub whoami > /dev/null 2>&1; then
  echo "Error: Not logged in to ClawHub. Run: clawhub login"
  exit 1
fi

echo "Publishing skills to ClawHub..."

for skill_dir in skills/*/; do
  skill_name=$(basename "$skill_dir")
  
  if [ ! -f "$skill_dir/SKILL.md" ]; then
    echo "  SKIP $skill_name (no SKILL.md)"
    continue
  fi

  echo "  Publishing $skill_name..."
  clawhub publish "$skill_dir" \
    --slug "$skill_name" \
    --name "$skill_name" \
    --version "1.0.0" \
    --changelog "Initial release" \
    --tags "latest,acedatacloud" \
    2>&1 || echo "  WARN: $skill_name publish failed (may already exist)"
done

echo "Done! View at https://clawhub.ai/skills?q=acedatacloud"
