# HTTP-first publishing connector expansion — 2026-11-09

## Scope and coverage

Existing CSDN, Juejin, WeChat Official Accounts, Weibo, Zhihu, CNBlogs,
Xiaohongshu, Toutiao, 51CTO, SegmentFault, OSChina and Bilibili are retained.
This release adds 12 connector entries and 13 skills, including completing the
existing Baijiahao cookie connector.

The implementation now favors direct HTTP execution: nine of the original
browser additions are cookie skills. With Baijiahao, ten of the thirteen skills
use HTTP. Login is initially captured by the ACE extension; execution does not
require a paired online browser. Three browser workflows remain where a suitable
HTTP write contract was not established.

| Skill | Execution | Output boundary |
|---|---|---|
| `jianshu` | HTTP | Draft; public submission stays in platform editor |
| `douyin` | Paired browser | Observed editor save/submission; needs online device |
| `netease` | HTTP | Draft; public submission stays in platform editor |
| `tencentcloud-community` | HTTP | Draft; public submission stays in platform editor |
| `aliyun-community` | HTTP | Draft; public submission stays in platform editor |
| `sohu` | HTTP | Draft; public submission stays in platform editor |
| `sspai` | Paired browser | Observed editor save/submission; needs online device |
| `infoq` | HTTP | Draft; public submission stays in platform editor |
| `huaweicloud-blog` | Paired browser | Observed editor save/submission; needs online device |
| `douban` | HTTP | Private note; not a draft/public post |
| `volcengine-community` | HTTP | Draft; public submission stays in platform editor |
| `modelscope` | HTTP | Body-only draft; title must be completed in editor |
| `baijiahao` | HTTP | HTML draft only |

## Implementation decisions

- Self-contained stdlib Python bundles: the shared HTTP helper's canonical source
  is `skills/_shared/publishing_http.py`; `scripts/sync_publishing_http.py` copies it
  into each bundle. Tests prevent stale copies and execute every bundle standalone.
- Cookies are scoped by origin, domain, hostOnly, path and expiry; redirects are
  refused. Error responses and credentials are not echoed. No write retries or
  browser fallbacks follow ambiguous writes.
- Jianshu requires an explicit notebook and Sohu an explicit subaccount. A failed
  second write preserves the original Jianshu/InfoQ draft ID for reconciliation.
- InfoQ, ModelScope and Douban accept literal text or explicitly prepared native
  editor JSON. They do not pretend Markdown text was rendered. Images are not
  re-hosted or silently removed.
- Cloud-community BYOC namespaces contain no hyphen (`tencentcloudcommunity`,
  `aliyuncommunity`, `volcenginecommunity`) to match the deployed runtime's alias
  parser. Their human-readable skill slugs remain hyphenated. No cloud-resource
  credentials are reused.
- An accepted save response reports `readback_verified=false`; it is not proof
  that the full article can be reopened or publicly viewed.

## Primary-source protocol research

- [MediaSync](https://github.com/yjmm10/MediaSync/tree/77ec95860fd1b0898459a6f401220e34cf80f31e), GPL-3.0: inspected HTTP request/response contracts for Jianshu, Netease, InfoQ, Tencent Cloud Community, Aliyun Developer, Volcengine and ModelScope in `packages/core/src/adapters/platforms/`.
- [Wechatsync](https://github.com/wechatsync/Wechatsync/tree/42f61e39e214b8d5377d09d788a716defc4abdc0), GPL-3.0: Baijiahao, Sohu and the current Douban topic/private-post contract. Old Douban note-autosave is not used.
- [cose](https://github.com/doocs/cose/tree/76c30c0bed8303168dd64288ae27f6094eae27ff), Apache-2.0: editor routes and modes for the remaining browser workflows.

The Python clients are independent implementations of protocol facts; no GPL
implementation was copied, translated or vendored. Source inspection is not live
verification. Unsupported platforms are not represented as fully published APIs.
Further candidates include 慕课手记、电子发烧友、华为开发者/鸿蒙、百度千帆、支付宝开放平台、大鱼号、一点号、雪球、什么值得买.

## Validation and release

- Local Skills root suite: 260 tests passed, including HTTP wire-contract,
  offline dry-run, standalone bundles, cookie boundaries, partial-write IDs,
  no retry, private-vs-draft status and remaining browser metadata.
- Local AuthBackend: 15 publishing/catalog tests passed; the real method
  validator accepts all entries and the complete 138-connector/143-method seed.
- The current user's stored connections contain none of these thirteen target
  platforms. Account-authenticated draft/private-post E2E therefore requires
  connecting those accounts after catalog rollout. No other user's credentials
  may be used. Deployment, catalog/package checks, and real upstream E2E are
  recorded separately in the release evidence.
- Merge/sync Skills before AuthBackend. Deploy the AuthBackend image, sync the
  connector catalog, read back every required skill and execution method, and
  verify package contents from the deployed catalog.
- Rollback catalog references before skills; never delete existing accounts or
  posts. No schema migration or browser protocol/digest change is introduced.
