# Amp source and official contribution

Canonical ownership: `platforms/amp/skills/<service>-by-acedatacloud/` in AceDataCloud/Skills. Do not modify shared `skills/`, other platforms, MCP APIs or a global provider catalog for this adapter.

Each directory is independently installable. The official target `ampcode/amp-contrib` currently keeps Skills under `.agents/skills/` and already includes a sibling `mcp.json` in `ui-preview`. There is no published special contribution template/CLA file at the checked main. A public pull request is a proposal, not acceptance.

For submission, copy each complete service directory to `.agents/skills/<same-name>/`, the READMEs use official image URLs so a single installed Skill stays self-contained. README references to the Ace source remain provenance links. Keep source and upstream payload byte-identical; update the open submission when the source changes, checking OPEN before each push.

The five `listing.json` files describe our service packaging; they are supplementary metadata, not an invented Amp registry manifest. Amp's executable contract is SKILL.md + mcp.json. No unrelated tools or model providers are bundled. No hosted personal/workspace share URLs are invented: an existing authorized account must import and publish them if needed after review.
