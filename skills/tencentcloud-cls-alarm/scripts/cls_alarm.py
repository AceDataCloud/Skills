#!/usr/bin/env python3
"""
Tencent Cloud CLS Alarm Management Tool

Manage CLS alarm policies, notice groups, shields (mute rules) and alarm
execution logs for AceDataCloud.

Console: https://console.cloud.tencent.com/cls/alarm/list?region=ap-hongkong

Quick examples:
  python3 $SKILL_DIR/scripts/cls_alarm.py alarms
  python3 $SKILL_DIR/scripts/cls_alarm.py alarm <alarm-id>
  python3 $SKILL_DIR/scripts/cls_alarm.py alarm-disable <alarm-id>
  python3 $SKILL_DIR/scripts/cls_alarm.py notices
  python3 $SKILL_DIR/scripts/cls_alarm.py shields
  python3 $SKILL_DIR/scripts/cls_alarm.py alarm-log --time 1d

Environment:
  Reads TENCENTCLOUD_SECRET_ID, TENCENTCLOUD_SECRET_KEY, TENCENTCLOUD_REGION
  from the environment.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timedelta


DEFAULT_REGION = os.environ.get("TENCENTCLOUD_REGION", "ap-hongkong")


def get_client(region: str = DEFAULT_REGION):
    try:
        from tencentcloud.cls.v20201016 import cls_client
        from tencentcloud.common import credential
    except ImportError:
        print(
            "ERROR: tencentcloud-sdk-python not installed.\n"
            "Run: pip3 install tencentcloud-sdk-python",
            file=sys.stderr,
        )
        sys.exit(1)

    secret_id = os.environ.get("TENCENTCLOUD_SECRET_ID")
    secret_key = os.environ.get("TENCENTCLOUD_SECRET_KEY")
    if not secret_id or not secret_key:
        print(
            "ERROR: TENCENTCLOUD_SECRET_ID and TENCENTCLOUD_SECRET_KEY must be set in env",
            file=sys.stderr,
        )
        sys.exit(1)

    cred = credential.Credential(secret_id, secret_key)
    return cls_client.ClsClient(cred, region)


def pp(data) -> None:
    print(json.dumps(data, indent=2, ensure_ascii=False, default=str))


def call(client, action: str, payload: dict) -> dict:
    """Call a CLS API action with a dict payload (uses from_json_string)."""
    from tencentcloud.cls.v20201016 import models

    req_cls = getattr(models, f"{action}Request", None)
    if req_cls is None:
        raise SystemExit(f"Unknown action: {action}")
    req = req_cls()
    req.from_json_string(json.dumps(payload))
    method = getattr(client, action)
    resp = method(req)
    return json.loads(resp.to_json_string())


def parse_time(value: str) -> int:
    """Parse '1h'/'30m'/'1d'/'7d' or ISO timestamp -> ms epoch."""
    value = value.strip()
    if value.isdigit():
        # Treat as seconds if 10 digits, else ms
        n = int(value)
        return n * 1000 if n < 10**12 else n
    if value[-1] in ("m", "h", "d") and value[:-1].isdigit():
        n = int(value[:-1])
        delta = {
            "m": timedelta(minutes=n),
            "h": timedelta(hours=n),
            "d": timedelta(days=n),
        }[value[-1]]
        return int((datetime.now() - delta).timestamp() * 1000)
    return int(datetime.fromisoformat(value).timestamp() * 1000)


# -----------------------------------------------------------------------------
# Alarm policies
# -----------------------------------------------------------------------------


def cmd_alarms(args):
    """List alarm policies (with optional filters)."""
    filters = []
    if args.name:
        filters.append({"Key": "name", "Values": [args.name]})
    if args.alarm_id:
        filters.append({"Key": "alarmId", "Values": [args.alarm_id]})
    if args.topic_id:
        filters.append({"Key": "topicId", "Values": [args.topic_id]})
    if args.enabled is not None:
        filters.append(
            {"Key": "enable", "Values": ["true" if args.enabled else "false"]}
        )

    payload = {"Filters": filters, "Offset": args.offset, "Limit": args.limit}
    data = call(get_client(args.region), "DescribeAlarms", payload)

    alarms = data.get("Alarms", [])
    total = data.get("TotalCount", len(alarms))

    if args.format == "json":
        pp(data)
        return

    print(f"Found {total} alarm policy(ies) (showing {len(alarms)}):\n")
    for a in alarms:
        enabled = a.get("Enable")
        status = a.get("Status")
        emoji = "●" if enabled else "○"
        level = {0: "Notice", 1: "Warning", 2: "Critical"}.get(
            a.get("AlarmLevel"), str(a.get("AlarmLevel"))
        )
        targets = a.get("AlarmTargets") or []
        topic_summary = ", ".join(t.get("TopicId", "?") for t in targets) or "-"
        notice_ids = ",".join(a.get("AlarmNoticeIds") or []) or "-"
        print(
            f"  {emoji} {a.get('AlarmId', ''):42s} {a.get('Name', '')[:40]:40s} "
            f"level={level:8s} period={a.get('AlarmPeriod', '-')}m trig={a.get('TriggerCount', '-')} "
            f"status={status}"
        )
        print(f"     topics: {topic_summary}")
        print(f"     notices: {notice_ids}")
        print()


def cmd_alarm(args):
    """Show a single alarm policy by ID (full detail)."""
    payload = {"Filters": [{"Key": "alarmId", "Values": [args.alarm_id]}], "Limit": 1}
    data = call(get_client(args.region), "DescribeAlarms", payload)
    alarms = data.get("Alarms", [])
    if not alarms:
        print(f"Alarm {args.alarm_id} not found", file=sys.stderr)
        sys.exit(1)
    pp(alarms[0])


def _build_alarm_payload(args, *, for_modify: bool = False) -> dict:
    """Build a Create/ModifyAlarm payload from CLI args + optional --json file."""
    payload: dict = {}
    if args.json:
        with open(args.json) as f:
            payload = json.load(f)

    if for_modify:
        payload["AlarmId"] = args.alarm_id

    if args.name:
        payload["Name"] = args.name
    if args.query is not None:
        target = {
            "TopicId": args.topic_id or "",
            "Query": args.query,
            "Number": 1,
            "StartTimeOffset": args.start_offset,
            "EndTimeOffset": args.end_offset,
            "SyntaxRule": args.syntax_rule,
        }
        if args.logset_id:
            target["LogsetId"] = args.logset_id
        payload["AlarmTargets"] = [target]
    if args.condition:
        payload["Condition"] = args.condition
    if args.period is not None:
        payload["AlarmPeriod"] = args.period
    if args.trigger_count is not None:
        payload["TriggerCount"] = args.trigger_count
    if args.level is not None:
        payload["AlarmLevel"] = args.level
    if args.notice_ids:
        payload["AlarmNoticeIds"] = [s for s in args.notice_ids.split(",") if s]
    if args.monitor_time:
        payload["MonitorTime"] = json.loads(args.monitor_time)
    if args.message_template is not None:
        payload["MessageTemplate"] = args.message_template
    if args.enable is not None:
        payload["Enable"] = args.enable
    if args.status is not None:
        payload["Status"] = args.status
    if not for_modify:
        payload.setdefault("MonitorObjectType", 0)
        payload.setdefault("MonitorTime", {"Type": "Period", "Time": 1})
        payload.setdefault("TriggerCount", 1)
        payload.setdefault("AlarmPeriod", 15)
    return payload


def cmd_alarm_create(args):
    payload = _build_alarm_payload(args, for_modify=False)
    if args.dry_run:
        pp(payload)
        return
    data = call(get_client(args.region), "CreateAlarm", payload)
    pp(data)


def cmd_alarm_modify(args):
    payload = _build_alarm_payload(args, for_modify=True)
    if args.dry_run:
        pp(payload)
        return
    data = call(get_client(args.region), "ModifyAlarm", payload)
    pp(data or {"ok": True, "alarm_id": args.alarm_id})


def cmd_alarm_delete(args):
    if not args.yes:
        print(
            f"Refusing to delete alarm {args.alarm_id} without --yes", file=sys.stderr
        )
        sys.exit(2)
    data = call(get_client(args.region), "DeleteAlarm", {"AlarmId": args.alarm_id})
    pp(data or {"ok": True, "deleted": args.alarm_id})


def cmd_alarm_toggle(args, enable: bool):
    data = call(
        get_client(args.region),
        "ModifyAlarm",
        {"AlarmId": args.alarm_id, "Status": enable},
    )
    pp(data or {"ok": True, "alarm_id": args.alarm_id, "status": enable})


# -----------------------------------------------------------------------------
# Notice groups
# -----------------------------------------------------------------------------


def cmd_notices(args):
    filters = []
    if args.name:
        filters.append({"Key": "name", "Values": [args.name]})
    if args.notice_id:
        filters.append({"Key": "alarmNoticeId", "Values": [args.notice_id]})
    payload = {"Filters": filters, "Offset": args.offset, "Limit": args.limit}
    data = call(get_client(args.region), "DescribeAlarmNotices", payload)
    notices = data.get("AlarmNotices", [])
    if args.format == "json":
        pp(data)
        return
    print(f"Found {data.get('TotalCount', len(notices))} notice group(s):\n")
    for n in notices:
        receivers = n.get("NoticeReceivers") or []
        webhooks = n.get("WebCallbacks") or []
        rcv_summary = (
            ",".join(
                f"{r.get('ReceiverType', '?')}:{len(r.get('ReceiverIds') or [])}"
                for r in receivers
            )
            or "-"
        )
        print(
            f"  {n.get('AlarmNoticeId', ''):42s} {n.get('Name', '')[:40]:40s} "
            f"type={n.get('Type', '-'):10s} receivers={rcv_summary} webhooks={len(webhooks)}"
        )


def cmd_notice(args):
    payload = {
        "Filters": [{"Key": "alarmNoticeId", "Values": [args.notice_id]}],
        "Limit": 1,
    }
    data = call(get_client(args.region), "DescribeAlarmNotices", payload)
    items = data.get("AlarmNotices", [])
    if not items:
        print(f"Notice {args.notice_id} not found", file=sys.stderr)
        sys.exit(1)
    pp(items[0])


def cmd_notice_create(args):
    if not args.json:
        print(
            "--json <file> with NoticeReceivers/WebCallbacks is required",
            file=sys.stderr,
        )
        sys.exit(2)
    with open(args.json) as f:
        payload = json.load(f)
    if args.name:
        payload["Name"] = args.name
    if args.type:
        payload["Type"] = args.type
    if args.dry_run:
        pp(payload)
        return
    data = call(get_client(args.region), "CreateAlarmNotice", payload)
    pp(data)


def cmd_notice_modify(args):
    if not args.json:
        print("--json <file> required for notice-modify", file=sys.stderr)
        sys.exit(2)
    with open(args.json) as f:
        payload = json.load(f)
    payload["AlarmNoticeId"] = args.notice_id
    if args.dry_run:
        pp(payload)
        return
    data = call(get_client(args.region), "ModifyAlarmNotice", payload)
    pp(data or {"ok": True, "notice_id": args.notice_id})


def cmd_notice_delete(args):
    if not args.yes:
        print(
            f"Refusing to delete notice {args.notice_id} without --yes", file=sys.stderr
        )
        sys.exit(2)
    data = call(
        get_client(args.region), "DeleteAlarmNotice", {"AlarmNoticeId": args.notice_id}
    )
    pp(data or {"ok": True, "deleted": args.notice_id})


# -----------------------------------------------------------------------------
# Shield rules
# -----------------------------------------------------------------------------


def cmd_shields(args):
    client = get_client(args.region)
    if args.notice_id:
        notice_ids = [args.notice_id]
    else:
        # DescribeAlarmShields requires AlarmNoticeId; iterate over all notices.
        notices = call(client, "DescribeAlarmNotices", {"Offset": 0, "Limit": 100})
        notice_ids = [
            n.get("AlarmNoticeId")
            for n in (notices.get("AlarmNotices") or [])
            if n.get("AlarmNoticeId")
        ]

    shields = []
    for nid in notice_ids:
        payload = {"AlarmNoticeId": nid, "Offset": args.offset, "Limit": args.limit}
        try:
            data = call(client, "DescribeAlarmShields", payload)
        except Exception as exc:  # noqa: BLE001
            print(f"  WARN: notice {nid}: {exc}", file=sys.stderr)
            continue
        for s in data.get("AlarmShields") or []:
            s.setdefault("AlarmNoticeId", nid)
            shields.append(s)

    if args.format == "json":
        pp({"AlarmShields": shields, "TotalCount": len(shields)})
        return
    print(f"Found {len(shields)} shield(s) across {len(notice_ids)} notice group(s):\n")
    for s in shields:
        ts_start = (
            datetime.fromtimestamp(s.get("StartTime", 0)).strftime("%Y-%m-%d %H:%M")
            if s.get("StartTime")
            else "-"
        )
        ts_end = (
            datetime.fromtimestamp(s.get("EndTime", 0)).strftime("%Y-%m-%d %H:%M")
            if s.get("EndTime")
            else "-"
        )
        print(
            f"  {s.get('TaskId', ''):42s} notice={s.get('AlarmNoticeId', '')} "
            f"type={s.get('Type', '-')} status={s.get('Status', '-')} "
            f"{ts_start} -> {ts_end}  reason={s.get('Reason', '-')[:40]}"
        )


def cmd_shield_create(args):
    payload = {
        "AlarmNoticeId": args.notice_id,
        "Type": args.type,
        "StartTime": int(args.start),
        "EndTime": int(args.end),
    }
    if args.reason:
        payload["Reason"] = args.reason
    if args.rule:
        payload["Rule"] = json.loads(args.rule)
    if args.dry_run:
        pp(payload)
        return
    data = call(get_client(args.region), "CreateAlarmShield", payload)
    pp(data)


def cmd_shield_modify(args):
    payload = {"TaskId": args.task_id}
    if args.start:
        payload["StartTime"] = int(args.start)
    if args.end:
        payload["EndTime"] = int(args.end)
    if args.type is not None:
        payload["Type"] = args.type
    if args.reason is not None:
        payload["Reason"] = args.reason
    if args.rule:
        payload["Rule"] = json.loads(args.rule)
    if args.dry_run:
        pp(payload)
        return
    data = call(get_client(args.region), "ModifyAlarmShield", payload)
    pp(data or {"ok": True, "task_id": args.task_id})


def cmd_shield_delete(args):
    if not args.yes:
        print(
            f"Refusing to delete shield {args.task_id} without --yes", file=sys.stderr
        )
        sys.exit(2)
    data = call(get_client(args.region), "DeleteAlarmShield", {"TaskId": args.task_id})
    pp(data or {"ok": True, "deleted": args.task_id})


# -----------------------------------------------------------------------------
# Alarm execution log (which alarms fired and when)
# -----------------------------------------------------------------------------


def cmd_alarm_log(args):
    to_ms = int(time.time() * 1000)
    from_ms = parse_time(args.time)
    payload = {
        "From": from_ms,
        "To": to_ms,
        "Query": args.query or "*",
        "Limit": args.limit,
        "Sort": args.sort,
        "UseNewAnalysis": True,
    }
    data = call(get_client(args.region), "GetAlarmLog", payload)
    if args.format == "json":
        pp(data)
        return
    results = data.get("Results", []) or []
    print(f"Found {len(results)} alarm log entr(ies):\n")
    for r in results:
        ts = datetime.fromtimestamp(r.get("Time", 0) / 1000).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        log = r.get("LogJson", "")
        try:
            d = json.loads(log)
            print(
                f"  [{ts}] alarm={d.get('alarm_name', '-')} alarm_id={d.get('alarm_id', '-')} "
                f"level={d.get('alarm_level', '-')} status={d.get('status', '-')}"
            )
            if d.get("trigger_query"):
                print(f"          query: {d['trigger_query'][:120]}")
        except Exception:
            print(f"  [{ts}] {log[:200]}")


# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Tencent CLS alarm management")
    p.add_argument(
        "--region",
        default=DEFAULT_REGION,
        help=f"CLS region (default: {DEFAULT_REGION})",
    )
    sub = p.add_subparsers(dest="command", required=True)

    def add_common_alarm_fields(sp, *, modify=False):
        sp.add_argument(
            "--json", help="Path to JSON file with full payload (other flags override)"
        )
        sp.add_argument("--name")
        sp.add_argument("--topic-id")
        sp.add_argument("--logset-id")
        sp.add_argument("--query", help="CLS query string for the alarm target")
        sp.add_argument(
            "--condition", help="Trigger condition expression, e.g. '$1.errors > 10'"
        )
        sp.add_argument(
            "--period", type=int, help="Alarm period in minutes (default: 15)"
        )
        sp.add_argument("--trigger-count", type=int)
        sp.add_argument("--start-offset", type=int, default=-15)
        sp.add_argument("--end-offset", type=int, default=0)
        sp.add_argument(
            "--syntax-rule", type=int, default=1, help="0=Lucene, 1=CQL (default: 1)"
        )
        sp.add_argument(
            "--level", type=int, choices=[0, 1, 2], help="0=Notice 1=Warning 2=Critical"
        )
        sp.add_argument("--notice-ids", help="Comma-separated AlarmNoticeIds")
        sp.add_argument(
            "--monitor-time", help='JSON, e.g. \'{"Type":"Period","Time":1}\''
        )
        sp.add_argument("--message-template")
        enable_group = sp.add_mutually_exclusive_group()
        enable_group.add_argument(
            "--enable", dest="enable", action="store_true", default=None
        )
        enable_group.add_argument("--disable", dest="enable", action="store_false")
        sp.add_argument("--status", type=lambda s: s.lower() in ("1", "true", "yes"))
        sp.add_argument("--dry-run", action="store_true")

    # ---- alarms ----
    sp = sub.add_parser("alarms", help="List alarm policies")
    sp.add_argument("--name")
    sp.add_argument("--alarm-id")
    sp.add_argument("--topic-id")
    sp.add_argument("--enabled", type=lambda s: s.lower() in ("1", "true", "yes"))
    sp.add_argument("--offset", type=int, default=0)
    sp.add_argument("--limit", type=int, default=100)
    sp.add_argument("--format", choices=["text", "json"], default="text")
    sp.set_defaults(func=cmd_alarms)

    sp = sub.add_parser("alarm", help="Show one alarm policy")
    sp.add_argument("alarm_id")
    sp.set_defaults(func=cmd_alarm)

    sp = sub.add_parser("alarm-create", help="Create alarm policy")
    add_common_alarm_fields(sp)
    sp.set_defaults(func=cmd_alarm_create)

    sp = sub.add_parser("alarm-modify", help="Modify alarm policy")
    sp.add_argument("alarm_id")
    add_common_alarm_fields(sp, modify=True)
    sp.set_defaults(func=cmd_alarm_modify)

    sp = sub.add_parser("alarm-delete", help="Delete alarm policy")
    sp.add_argument("alarm_id")
    sp.add_argument("--yes", action="store_true", help="Confirm destructive op")
    sp.set_defaults(func=cmd_alarm_delete)

    sp = sub.add_parser("alarm-enable", help="Enable an alarm (Status=true)")
    sp.add_argument("alarm_id")
    sp.set_defaults(func=lambda a: cmd_alarm_toggle(a, True))

    sp = sub.add_parser("alarm-disable", help="Disable an alarm (Status=false)")
    sp.add_argument("alarm_id")
    sp.set_defaults(func=lambda a: cmd_alarm_toggle(a, False))

    # ---- notices ----
    sp = sub.add_parser("notices", help="List notice groups")
    sp.add_argument("--name")
    sp.add_argument("--notice-id")
    sp.add_argument("--offset", type=int, default=0)
    sp.add_argument("--limit", type=int, default=100)
    sp.add_argument("--format", choices=["text", "json"], default="text")
    sp.set_defaults(func=cmd_notices)

    sp = sub.add_parser("notice", help="Show one notice group")
    sp.add_argument("notice_id")
    sp.set_defaults(func=cmd_notice)

    sp = sub.add_parser("notice-create", help="Create notice group (requires --json)")
    sp.add_argument("--json", required=True)
    sp.add_argument("--name")
    sp.add_argument("--type", choices=["Trigger", "Recovery", "All"])
    sp.add_argument("--dry-run", action="store_true")
    sp.set_defaults(func=cmd_notice_create)

    sp = sub.add_parser("notice-modify", help="Modify notice group (requires --json)")
    sp.add_argument("notice_id")
    sp.add_argument("--json", required=True)
    sp.add_argument("--dry-run", action="store_true")
    sp.set_defaults(func=cmd_notice_modify)

    sp = sub.add_parser("notice-delete", help="Delete notice group")
    sp.add_argument("notice_id")
    sp.add_argument("--yes", action="store_true")
    sp.set_defaults(func=cmd_notice_delete)

    # ---- shields ----
    sp = sub.add_parser("shields", help="List alarm shield (mute) rules")
    sp.add_argument("--notice-id")
    sp.add_argument("--offset", type=int, default=0)
    sp.add_argument("--limit", type=int, default=100)
    sp.add_argument("--format", choices=["text", "json"], default="text")
    sp.set_defaults(func=cmd_shields)

    sp = sub.add_parser("shield-create", help="Create alarm shield")
    sp.add_argument("--notice-id", required=True)
    sp.add_argument("--start", required=True, help="Unix seconds")
    sp.add_argument("--end", required=True, help="Unix seconds")
    sp.add_argument("--type", type=int, default=1, help="1=All 2=Custom (default: 1)")
    sp.add_argument("--reason")
    sp.add_argument("--rule", help="JSON for custom rule (when --type 2)")
    sp.add_argument("--dry-run", action="store_true")
    sp.set_defaults(func=cmd_shield_create)

    sp = sub.add_parser("shield-modify", help="Modify alarm shield")
    sp.add_argument("task_id")
    sp.add_argument("--start")
    sp.add_argument("--end")
    sp.add_argument("--type", type=int)
    sp.add_argument("--reason")
    sp.add_argument("--rule")
    sp.add_argument("--dry-run", action="store_true")
    sp.set_defaults(func=cmd_shield_modify)

    sp = sub.add_parser("shield-delete", help="Delete alarm shield")
    sp.add_argument("task_id")
    sp.add_argument("--yes", action="store_true")
    sp.set_defaults(func=cmd_shield_delete)

    # ---- alarm log ----
    sp = sub.add_parser(
        "alarm-log", help="Query alarm execution log (which alarms fired)"
    )
    sp.add_argument(
        "--time", default="1d", help="Time range: 30m/1h/6h/1d/7d (default: 1d)"
    )
    sp.add_argument("--query", default="*")
    sp.add_argument("--limit", type=int, default=100)
    sp.add_argument("--sort", choices=["asc", "desc"], default="desc")
    sp.add_argument("--format", choices=["text", "json"], default="text")
    sp.set_defaults(func=cmd_alarm_log)

    return p


def main():
    args = build_parser().parse_args()
    try:
        args.func(args)
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
