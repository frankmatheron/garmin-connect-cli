from __future__ import annotations

import json
import sys
from pathlib import Path


def _output(data: object, pretty: bool) -> None:
    if pretty:
        if isinstance(data, list):
            for item in data:
                wid = item.get("workoutId", "?")
                name = item.get("workoutName", "(unnamed)")
                print(f"{wid}\t{name}")
        elif isinstance(data, dict):
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            print(data)
    else:
        print(json.dumps(data, ensure_ascii=False))


def run(api, args) -> int:
    cmd = args.command

    if cmd == "list":
        workouts = api.get_workouts()
        _output(workouts, args.pretty)
        return 0

    if cmd == "get":
        workout = api.get_workout_by_id(args.id)
        _output(workout, args.pretty)
        return 0

    if cmd == "create":
        results = []
        for fname in args.files:
            if fname == "-":
                payload = json.load(sys.stdin)
            else:
                payload = json.loads(Path(fname).read_text())
            result = api.upload_workout(payload)
            results.append(result)
        _output(results, args.pretty)
        return 0

    if cmd == "delete":
        api.delete_workout(args.id)
        _output({"deleted": args.id}, args.pretty)
        return 0

    if cmd == "download":
        data = api.download_workout(args.id)
        out_path = Path(args.out) if args.out else Path(f"workout_{args.id}.fit")
        if isinstance(data, (bytes, bytearray)):
            out_path.write_bytes(data)
        else:
            out_path.write_text(json.dumps(data, ensure_ascii=False))
        print(str(out_path))
        return 0

    print(f"unknown workouts command: {cmd}", file=sys.stderr)
    return 1
