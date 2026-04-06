#!/usr/bin/env node

import { existsSync, mkdirSync, cpSync, readdirSync } from "fs";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const skillsSrc = resolve(__dirname, "..", "skills");

const args = process.argv.slice(2);
const command = args[0];

function printUsage() {
  console.log(`
Usage: npx @acedatacloud/skills <command> [options]

Commands:
  install [--target <dir>]   Copy skills into your project
  list                       List all available skills

Options:
  --target <dir>   Target directory (default: .agents/skills)

Examples:
  npx @acedatacloud/skills install                          # → .agents/skills/
  npx @acedatacloud/skills install --target .claude/skills  # → .claude/skills/
  npx @acedatacloud/skills install --target .github/skills  # → .github/skills/
  npx @acedatacloud/skills list
`);
}

function listSkills() {
  const skills = readdirSync(skillsSrc, { withFileTypes: true })
    .filter((d) => d.isDirectory() && !d.name.startsWith("_"))
    .map((d) => d.name)
    .sort();
  console.log(`Available skills (${skills.length}):\n`);
  skills.forEach((s) => console.log(`  - ${s}`));
}

function installSkills(target) {
  const dest = resolve(process.cwd(), target);
  mkdirSync(dest, { recursive: true });

  const skills = readdirSync(skillsSrc, { withFileTypes: true })
    .filter((d) => d.isDirectory() && !d.name.startsWith("_"))
    .map((d) => d.name);

  let count = 0;
  for (const skill of skills) {
    const src = resolve(skillsSrc, skill);
    const dst = resolve(dest, skill);
    cpSync(src, dst, { recursive: true });
    count++;
  }
  console.log(`Installed ${count} skills to ${dest}`);
}

if (!command || command === "--help" || command === "-h") {
  printUsage();
} else if (command === "list") {
  listSkills();
} else if (command === "install") {
  const targetIdx = args.indexOf("--target");
  const target = targetIdx !== -1 ? args[targetIdx + 1] : ".agents/skills";
  if (!target) {
    console.error("Error: --target requires a directory path");
    process.exit(1);
  }
  installSkills(target);
} else {
  console.error(`Unknown command: ${command}`);
  printUsage();
  process.exit(1);
}
