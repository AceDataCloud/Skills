# Tencent Cloud Authentication

All `tencentcloud-*` skills authenticate with the same SecretId / SecretKey pair via the official Tencent Cloud Python SDK.

## Get Your Credentials

1. Sign in to [Tencent Cloud Console](https://console.cloud.tencent.com/cam/capi)
2. Navigate to **Access Management → API Keys → Create Key**
3. You'll get a **SecretId** (starts with `AKID...`) and a **SecretKey** that's displayed exactly once — save it before closing the page.

> ⚠️ **Use a sub-account, not your main account.** Create a CAM sub-user with only the policies the skill needs (e.g. `QcloudCOSReadOnlyAccess` for read-only COS, `QcloudCLSReadOnlyAccess` for log queries) and generate the keys for that sub-account. Limits the blast radius if the credentials leak.

## Setup

The Tencent Cloud SDK reads credentials from these environment variables:

| Variable | Description | Example |
|---|---|---|
| `TENCENTCLOUD_SECRET_ID` | API SecretId | `AKIDxxxxxxxxxxxx` |
| `TENCENTCLOUD_SECRET_KEY` | API SecretKey (sensitive) | `xxxxxxxxxxxxxxxx` |
| `TENCENTCLOUD_REGION` | Default region | `ap-hongkong`, `ap-guangzhou`, ... |

**Local dev — `.env` file**:

```bash
TENCENTCLOUD_SECRET_ID=AKID...
TENCENTCLOUD_SECRET_KEY=...
TENCENTCLOUD_REGION=ap-hongkong
```

Load it before running any tool:

```bash
set -a; source .env; set +a
```

> ⚠️ **Important:** Add `.env` to your `.gitignore` — never commit credentials to git.

**Agent usage** (Claude / Studio / etc.): If you've installed the [腾讯云 connector](https://auth.acedata.cloud/user/connections) on AceDataCloud, your encrypted credentials are auto-injected as the env vars above when the agent runs any `tencentcloud-*` skill — no manual `.env` setup needed.

## Common regions

| Region code | Location |
|---|---|
| `ap-hongkong` | Hong Kong, China |
| `ap-guangzhou` | Guangzhou |
| `ap-beijing` | Beijing |
| `ap-shanghai` | Shanghai |
| `ap-singapore` | Singapore |
| `ap-tokyo` | Tokyo |
| `eu-frankfurt` | Frankfurt |
| `na-siliconvalley` | Silicon Valley |
| `na-ashburn` | Ashburn (Virginia) |

Full list: [Tencent Cloud regions and AZs](https://www.tencentcloud.com/document/product/213/6091).

## Verifying credentials

A quick sanity check that doesn't cost anything:

```python
from tencentcloud.common import credential
from tencentcloud.cam.v20190116 import cam_client, models

cred = credential.EnvironmentVariableCredential().get_credential()
client = cam_client.CamClient(cred, "ap-guangzhou")
resp = client.GetUserAppId(models.GetUserAppIdRequest())
print("OK, AppId =", resp.AppId)
```

Returns your Tencent Cloud `AppId` (a numeric account identifier). Any 4xx tells you the keys are wrong / expired / lack `QcloudCamReadOnlyAccess`.

## Dependencies

```bash
pip install tencentcloud-sdk-python
```

Service-specific add-ons used by individual skills:

```bash
pip install cos-python-sdk-v5      # tencentcloud-cos
pip install kubernetes              # tencentcloud-tke (kubeconfig handling)
```
