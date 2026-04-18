from __future__ import annotations

import json
import sys


def _output(data: object, pretty: bool) -> None:
    if pretty:
        if isinstance(data, list):
            for item in data:
                aid = item.get("activityId", "?")
                name = item.get("activityName", "(unnamed)")
                date = item.get("startTimeLocal", "?")
                dist = item.get("distance", 0)
                dur = item.get("duration", 0)
                dist_km = dist / 1000 if dist else 0
                dur_min = dur / 60 if dur else 0
                print(f"{aid}\t{date}\t{dist_km:.2f}km\t{dur_min:.1f}min\t{name}")
        elif isinstance(data, dict):
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            print(data)
    else:
        print(json.dumps(data, ensure_ascii=False))


def run(api, args) -> int:
    cmd = args.command

    if cmd == "list":
        activities = api.get_activities_by_date(args.start, args.end, args.type)
        _output(activities, args.pretty)
        return 0

    if cmd == "get":
        activity = api.get_activity(args.id)
        _output(activity, args.pretty)
        return 0

    if cmd == "splits":
        splits = api.get_activity_splits(args.id)
        _output(splits, args.pretty)
        return 0

    if cmd == "details":
        details = api.get_activity_details(args.id)
        _output(details, args.pretty)
        return 0

    if cmd == "hr":
        hr = api.get_activity_hr_in_timezones(args.id)
        _output(hr, args.pretty)
        return 0

    if cmd == "rename":
        api.set_activity_name(args.id, args.name)
        print(f"renamed {args.id} → {args.name}")
        return 0

    if cmd == "retype":
        api.set_activity_type(args.id, args.type_id, args.type_key, args.parent_type_id)
        print(f"retyped {args.id} → {args.type_key}")
        return 0

    print(f"unknown activities command: {cmd}", file=sys.stderr)
    return 1
