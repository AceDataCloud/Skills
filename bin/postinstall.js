import { existsSync } from "fs";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));

// Only show install hint during explicit npm install (not CI/scripts)
if (process.env.npm_config_global !== "true" && !process.env.CI) {
  console.log(
    "\n📦 AceDataCloud Skills installed. To copy skills into your project:\n"
  );
  console.log("  npx acedatacloud-skills install                          # → .agents/skills/");
  console.log("  npx acedatacloud-skills install --target .claude/skills  # → .claude/skills/");
  console.log("  npx acedatacloud-skills install --target .github/skills  # → .github/skills/\n");
}
