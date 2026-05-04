---
name: tencentcloud-cls-alarm
description: |
  Manage Tencent Cloud CLS alarm policies, notice groups, shields and
  alarm execution logs. Use when the user asks to: list / create /
  modify / delete CLS alarms, enable or disable alarms, manage notice
  recipients (SMS / email / webhook), mute alarms during deploys, or
  view which alarms fired and when. For searching the underlying log
  content, use the companion `tencentcloud-cls` skill.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
connections: [tencentcloud]
---

# Tencent Cloud CLS — Alarm Management

CRUD on CLS alarm policies, notice groups, mute shields, and the alarm execution log.

> **Setup:** See [tencentcloud authentication](../_shared/tencentcloud.md). Defaults to `TENCENTCLOUD_REGION` from env; CLS alarms live per-region.
>
> **Companion skill:** `tencentcloud-cls` for log content search.

## CLI (preferred)

The skill ships [`scripts/cls_alarm.py`](scripts/cls_alarm.py) — wraps every alarm / notice / shield operation as a subcommand.

```bash
A=$SKILL_DIR/scripts/cls_alarm.py

python3 $A alarms                              # list policies
python3 $A alarm <alarm-id>                    # full detail
python3 $A alarm-disable <alarm-id>            # quick mute (Status=false)
python3 $A alarm-enable  <alarm-id>
python3 $A alarm-create --json /tmp/alarm.json --dry-run
python3 $A alarm-modify <alarm-id> --condition '$1.cnt > 20'
python3 $A alarm-delete <alarm-id> --yes       # destructive

python3 $A notices                             # notice groups
python3 $A notice <notice-id>

python3 $A shields                             # mute rules
python3 $A shield-create --notice-id <notice-id> --start $(date +%s) --end $(date -v+2H +%s) --type 1 --reason "deploy"

python3 $A alarm-log --time 6h                 # firing history
```

For the rare schema field the CLI doesn't surface, fall through to the raw SDK examples below.

## When to Use

- Inspect existing alarm policies (filter by name, enabled flag)
- Create a new log-based alarm: CQL/SQL query → trigger condition → notice group
- Modify thresholds, query, period, recipients
- Quick enable / disable to mute during incidents
- Manage notice groups (recipients: users, groups, webhooks, with escalation)
- Time-bounded shield rules to mute during deploys
- Pull the alarm execution log to see *which* alarms fired and when

## Dependencies

```bash
pip install tencentcloud-sdk-python
```

## Quick start

```python
import os
import json
from tencentcloud.common import credential
from tencentcloud.cls.v20201016 import cls_client, models

cred = credential.EnvironmentVariableCredential().get_credential()
client = cls_client.ClsClient(cred, os.environ["TENCENTCLOUD_REGION"])
```

## Key concepts

| Object | API methods | What it is |
|---|---|---|
| Alarm policy | `DescribeAlarms` / `CreateAlarm` / `ModifyAlarm` / `DeleteAlarm` | Query against one or more topics + condition + notice groups |
| Notice group | `DescribeAlarmNotices` / `CreateAlarmNotice` / … | Recipients (users / groups / webhooks) + escalation |
| Shield | `DescribeAlarmShields` / `CreateAlarmShield` / … | Time-bounded mute scoped to a notice group |
| Alarm log | `GetAlarmLog` | Firing history |

## Workflows

### List alarm policies

```python
req = models.DescribeAlarmsRequest()
req.Limit = 100
# Optional filters: req.Filters = [{"Key": "name", "Values": ["DeepSeek"]}]
resp = client.DescribeAlarms(req)
for a in resp.Alarms:
    print(a.AlarmId, a.Name, "Enable=", a.Enable, "Status=", a.Status)
```

### Get a single alarm policy in full

```python
req = models.DescribeAlarmsRequest()
req.Filters = [{"Key": "alarmId", "Values": ["<alarm-id>"]}]
resp = client.DescribeAlarms(req)
print(json.dumps(resp.Alarms[0]._serialize(), indent=2, ensure_ascii=False))
```

### Create an alarm

```python
req = models.CreateAlarmRequest()
req.Name = "OpenAI 5xx burst"
req.AlarmTargets = [{
    "TopicId": "<trace-topic-id>",
    "Query": "* | select count(*) as cnt where status_code >= 500",
    "Number": 1,
    "StartTimeOffset": -5,
    "EndTimeOffset": 0,
    "SyntaxRule": 1,             # 1 = CQL, 0 = Lucene
}]
req.MonitorTime = {"Type": "Period", "Time": 1}
req.Condition = "$1.cnt > 10"
req.AlarmPeriod = 5              # evaluate every 5 minutes
req.TriggerCount = 1             # fire after 1 consecutive match
req.AlarmLevel = 2               # 0=Notice, 1=Warning, 2=Critical
req.AlarmNoticeIds = ["<notice-id-a>", "<notice-id-b>"]
req.MonitorObjectType = 0
req.Enable = True

resp = client.CreateAlarm(req)
print("Created", resp.AlarmId)
```

### Quick enable / disable

```python
req = models.ModifyAlarmRequest()
req.AlarmId = "<alarm-id>"
req.Status = False               # mute (Status — runtime), keep Enable=True
client.ModifyAlarm(req)
```

> **`Enable` vs `Status`** are different fields. `Enable=False` archives the alarm definition; `Status=False` is the everyday on/off switch you want for muting.

### Modify thresholds without rewriting the whole payload

```python
req = models.ModifyAlarmRequest()
req.AlarmId = "<alarm-id>"
req.Condition = "$1.cnt > 20"
req.AlarmPeriod = 10
client.ModifyAlarm(req)
```

### Delete (destructive)

```python
# Confirm with the user first — there's no undo.
req = models.DeleteAlarmRequest()
req.AlarmId = "<alarm-id>"
client.DeleteAlarm(req)
```

### Manage notice groups

```python
# List
req = models.DescribeAlarmNoticesRequest()
req.Limit = 100
for n in client.DescribeAlarmNotices(req).AlarmNotices:
    print(n.AlarmNoticeId, n.Name, n.Type)

# Create
req = models.CreateAlarmNoticeRequest()
req.Name = "Ops on-call"
req.Type = "Trigger"             # Trigger | Recovery | All
req.NoticeReceivers = [{
    "ReceiverType": "Uin",
    "ReceiverIds": [123456],
    "ReceiverChannels": ["Email", "Sms"],
    "StartTime": "00:00:00",
    "EndTime": "23:59:59",
}]
req.WebCallbacks = [{
    "Url": "https://hooks.example.com/cls",
    "CallbackType": "WeCom",
    "Method": "POST",
}]
resp = client.CreateAlarmNotice(req)
```

### Time-bounded shield (mute during deploy)

```python
import time
req = models.CreateAlarmShieldRequest()
req.AlarmNoticeId = "<notice-id>"
req.StartTime = int(time.time())
req.EndTime = int(time.time()) + 7200       # 2 hours
req.Type = 1                                # 1 = full shield, 2 = partial
req.Reason = "Deploy <git-sha>"
client.CreateAlarmShield(req)
```

### Inspect alarm firing history

```python
req = models.GetAlarmLogRequest()
req.From = int((time.time() - 86400) * 1000)
req.To = int(time.time() * 1000)
req.Query = 'alarm_name:"OpenAI*"'
req.Limit = 100
resp = client.GetAlarmLog(req)
for line in resp.Results:
    print(line.Time, line.LogJson)
```

## Cloning an alarm

The fastest way to create a similar alarm is to read the existing one, strip read-only fields, tweak, and re-create:

```python
import json
existing = client.DescribeAlarms(models.DescribeAlarmsRequest(Filters=[{"Key": "alarmId", "Values": ["<src-id>"]}])).Alarms[0]
payload = json.loads(json.dumps(existing._serialize()))      # deep clone
for k in ("AlarmId", "CreateTime", "UpdateTime"):
    payload.pop(k, None)
payload["Name"] = "OpenAI 5xx burst v2"
# ...edit other fields...
req = models.CreateAlarmRequest()
req.from_json_string(json.dumps(payload))
print(client.CreateAlarm(req).AlarmId)
```

## Important reminders

- **Always preview the payload** (`json.dumps(req._serialize(), indent=2)`) before `CreateAlarm` / `ModifyAlarm` — schema is strict and errors are unhelpful.
- Destructive ops (`DeleteAlarm`, `DeleteAlarmNotice`, `DeleteAlarmShield`) need explicit user confirmation in chat before running.
- `Enable` (archived?) vs `Status` (currently on?) are *different* fields. Use `Status` for everyday muting.
- Shield rules are scoped to a single `AlarmNoticeId`. Iterate over all notice IDs to list all shields globally.
- Default region is `ap-hongkong`; pass another region via `cls_client.ClsClient(cred, "ap-singapore")` if needed.

## Console links

- Alarm console: <https://console.cloud.tencent.com/cls/alarm/list>
- Alarm API reference: <https://www.tencentcloud.com/document/product/614/56473>
