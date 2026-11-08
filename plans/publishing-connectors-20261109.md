# Publishing connector expansion — 2026-11-09

## Coverage before this change

Inventory checked against Skills `a197f72` and AuthBackend `978dfc1`.
CSDN and Juejin already have executable cookie skills. Of the distinct platforms
in the supplied screenshot, WeChat Official Accounts, Weibo, Zhihu, Juejin,
CNBlogs, Xiaohongshu, Toutiao, 51CTO, SegmentFault, OSChina and Bilibili already
have connector/skill entries. Xiaohongshu's skill includes image and long-form
notes. Existing 51CTO/OSChina skills are draft-oriented. Baijiahao had a cookie
connector with an empty required-skills list. Do not equate any catalog entry
with live publication readiness.

## Additions

| Skill | Source module in cose | Mode / boundary |
|---|---|---|
| `jianshu` | `jianshu.js` | Paired local browser; draft and submission result verified from UI |
| `douyin` | `douyin.js` | Paired local browser; draft and submission result verified from UI |
| `netease` | `wangyihao.js` | Paired local browser; draft and submission result verified from UI |
| `tencentcloud-community` | `tencentcloud.js` | Paired local browser; draft and submission result verified from UI |
| `aliyun-community` | `aliyun.js` | Paired local browser; draft and submission result verified from UI |
| `sohu` | `sohu.js` | Paired local browser; draft and submission result verified from UI |
| `sspai` | `sspai.js` | Paired local browser; draft and submission result verified from UI |
| `infoq` | `infoq.js` | Paired local browser; draft and submission result verified from UI |
| `huaweicloud-blog` | `huaweicloud.js` | Paired local browser; draft and submission result verified from UI |
| `douban` | `douban.js` | Paired local browser; draft and submission result verified from UI |
| `volcengine-community` | `volcengine.js` | Paired local browser; draft and submission result verified from UI |
| `modelscope` | `modelscope.js` | Paired local browser; draft and submission result verified from UI |
| `baijiahao` | Wechatsync `baijiahao.ts`; cose detection config | Stdlib cookie client; account lookup + HTML draft only |

Douyin long-article and image modes share one connector; video/TikTok is outside
this skill. Cloud communities use separate namespaces from infrastructure
connectors. Each browser skill is self-contained and activates only standard
browser facades for its exact HTTPS origin. SSO credentials remain user-operated;
login hosts and arbitrary external content origins are not added to permissions.

## Open-source evidence and licensing

- [doocs/cose](https://github.com/doocs/cose/tree/76c30c0bed8303168dd64288ae27f6094eae27ff), Apache-2.0: inspected `packages/core/src/platforms/` and `packages/detection/src/`. Its adapter success often means editor fill, not publication. Per-skill links pin the exact inspected source. No extension JavaScript is embedded or executed by the new skills.
- [Wechatsync](https://github.com/wechatsync/Wechatsync/tree/42f61e39e214b8d5377d09d788a716defc4abdc0), GPL-3.0: inspected Baijiahao request/response fields to implement an independent Python HTTP client. No GPL code was copied, translated or vendored. The save endpoint produces a draft; it is not represented as a public publish API.

Further source candidates include 慕课手记、电子发烧友、华为开发者/鸿蒙、百度千帆、支付宝开放平台、大鱼号、一点号、雪球、什么值得买. These remain unimplemented here: a platform name or editor route alone is insufficient to promise a supported end-to-end publishing flow.

## Verification and release boundary

- Browser policy tests validate facade/command/capability coverage, exact origin,
  provider identity, operation classification, and package discoverability.
- Baijiahao tests use mocked responses for auth, JSON/JSONP save, redirect refusal,
  cookie scope, dry-run, malformed responses, credential-safe failures and
  ambiguous writes. No test creates an article on a real account.
- AuthBackend tests exercise its real connection-method validator for every new
  catalog item and preserve Baijiahao's existing cookie method identity.
- Existing runtime/browser transport is reused; no protocol or digest changes.
- Before claiming live support, pair a device, log into each target, save/reopen
  a small authorized draft, and separately authorize a public publication to
  verify its terminal status/link. Account permissions, WAF and editor drift
  may still block individual platforms.

Merge/sync Skills before AuthBackend's connector catalog so required skill
identifiers resolve. No database migration or frontend build is required.
Rollback by reverting the catalog additions first; existing accounts and
articles are not deleted. Revert the skill addition only after removing its
catalog references. This task opens PRs; it does not merge or deploy them.

## Local verification results

- Skills root unittest suite: 245 passed.
- AuthBackend publishing catalog tests plus existing seed-count check: 15 passed; Ruff check/format passed.
- Twelve browser skills parsed and activated by the actual PlatformService parser and BrowserFacadeLoader at `84d6cf3fe760400a44e71f7485c9cc12310ceb7a`, using synthetic session state and the new connector policies; no account or browser was accessed.
- Thirteen skills passed the skill-creator standard metadata/body validation projection; repository-specific execution metadata is covered by the browser contract tests.
- `git diff --check` passed in both repositories. Live-account E2E is pending.
