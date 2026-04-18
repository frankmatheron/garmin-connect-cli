from __future__ import annotations

import json
import sys


def _output(data: object, pretty: bool) -> None:
    if pretty:
        if isinstance(data, list):
            for item in data:
                sid = item.get("scheduledWorkoutId", "?")
                date = item.get("date", "?")
                name = item.get("workoutName", "")
                print(f"{date}\t{sid}\t{name}")
        elif isinstance(data, dict):
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            print(data)
    else:
        print(json.dumps(data, ensure_ascii=False))


def run(api, args) -> int:
    cmd = args.command

    if cmd == "list":
        scheduled = api.get_scheduled_workouts(args.year, args.month)
        _output(scheduled, args.pretty)
        return 0

    if cmd == "add":
        result = api.schedule_workout(args.workout_id, args.date)
        _output(result, args.pretty)
        return 0

    if cmd == "remove":
        api.unschedule_workout(args.scheduled_id)
        _output({"removed": args.scheduled_id}, args.pretty)
        return 0

    print(f"unknown calendar command: {cmd}", file=sys.stderr)
    return 1
