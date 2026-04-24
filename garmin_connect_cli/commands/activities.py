from __future__ import annotations

import json
import sys
from pathlib import Path


def _output(data: object, pretty: bool) -> None:
    if pretty:
        if isinstance(data, list):
            for item in data:
                if not isinstance(item, dict):
                    print(item)
                    continue
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

    if cmd == "recent":
        activities = api.get_activities(args.offset, args.limit, args.type)
        _output(activities, args.pretty)
        return 0

    if cmd == "count":
        _output({"count": api.count_activities()}, args.pretty)
        return 0

    if cmd == "types":
        _output(api.get_activity_types(), args.pretty)
        return 0

    if cmd == "last":
        _output(api.get_last_activity(), args.pretty)
        return 0

    if cmd == "fordate":
        _output(api.get_activities_fordate(args.date), args.pretty)
        return 0

    if cmd == "get":
        _output(api.get_activity(args.id), args.pretty)
        return 0

    if cmd == "splits":
        _output(api.get_activity_splits(args.id), args.pretty)
        return 0

    if cmd == "typed-splits":
        _output(api.get_activity_typed_splits(args.id), args.pretty)
        return 0

    if cmd == "split-summaries":
        _output(api.get_activity_split_summaries(args.id), args.pretty)
        return 0

    if cmd == "details":
        _output(
            api.get_activity_details(args.id, args.max_chart, args.max_poly),
            args.pretty,
        )
        return 0

    if cmd == "hr":
        _output(api.get_activity_hr_in_timezones(args.id), args.pretty)
        return 0

    if cmd == "power":
        _output(api.get_activity_power_in_timezones(args.id), args.pretty)
        return 0

    if cmd == "weather":
        _output(api.get_activity_weather(args.id), args.pretty)
        return 0

    if cmd == "exercise-sets":
        _output(api.get_activity_exercise_sets(args.id), args.pretty)
        return 0

    if cmd == "gear":
        _output(api.get_activity_gear(args.id), args.pretty)
        return 0

    if cmd == "add-gear":
        api.add_gear_to_activity(args.gear_uuid, args.id)
        print(f"added gear {args.gear_uuid} → activity {args.id}")
        return 0

    if cmd == "remove-gear":
        api.remove_gear_from_activity(args.gear_uuid, args.id)
        print(f"removed gear {args.gear_uuid} from activity {args.id}")
        return 0

    if cmd == "rename":
        api.set_activity_name(args.id, args.name)
        print(f"renamed {args.id} → {args.name}")
        return 0

    if cmd == "retype":
        api.set_activity_type(args.id, args.type_id, args.type_key, args.parent_type_id)
        print(f"retyped {args.id} → {args.type_key}")
        return 0

    if cmd == "delete":
        api.delete_activity(args.id)
        print(f"deleted {args.id}")
        return 0

    if cmd == "download":
        fmt = args.format.upper()
        from garminconnect import Garmin

        fmt_enum = getattr(Garmin.ActivityDownloadFormat, fmt)
        data = api.download_activity(args.id, fmt_enum)
        ext = {"ORIGINAL": "zip", "TCX": "tcx", "GPX": "gpx", "KML": "kml", "CSV": "csv"}[fmt]
        out_path = Path(args.out) if args.out else Path(f"activity_{args.id}.{ext}")
        out_path.write_bytes(data)
        print(str(out_path))
        return 0

    if cmd == "upload":
        result = api.upload_activity(args.file)
        _output(result if isinstance(result, (dict, list)) else {"ok": True}, args.pretty)
        return 0

    if cmd == "import":
        result = api.import_activity(args.file)
        _output(result if isinstance(result, (dict, list)) else {"ok": True}, args.pretty)
        return 0

    if cmd == "manual-create":
        result = api.create_manual_activity(
            args.start_datetime,
            args.timezone,
            args.type_key,
            args.distance_km,
            args.duration_min,
            args.name,
        )
        _output(result, args.pretty)
        return 0

    print(f"unknown activities command: {cmd}", file=sys.stderr)
    return 1
