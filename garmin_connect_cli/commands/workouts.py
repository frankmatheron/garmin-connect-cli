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


_PAGE_SIZE = 100  # Garmin's per-request max for the workouts endpoint.


def _list_all_workouts(api, limit: int | None = None) -> list[dict]:
    """Page through `get_workouts(start, limit)` until exhausted (or `limit`
    results collected). The underlying endpoint caps each call at 100."""
    out: list[dict] = []
    start = 0
    while True:
        page_size = _PAGE_SIZE
        if limit is not None:
            remaining = limit - len(out)
            if remaining <= 0:
                break
            page_size = min(page_size, remaining)
        page = api.get_workouts(start=start, limit=page_size)
        if not page:
            break
        # Defensive truncate: if the API returned more than asked
        # (shouldn't happen, but don't trust it for `--limit` correctness).
        if len(page) > page_size:
            page = page[:page_size]
        out.extend(page)
        if len(page) < page_size:
            break
        start += len(page)
    return out


def run(api, args) -> int:
    cmd = args.command

    if cmd == "list":
        limit = getattr(args, "limit", None)
        workouts = _list_all_workouts(api, limit=limit)
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

    if cmd == "update":
        if args.file == "-":
            payload = json.load(sys.stdin)
        else:
            payload = json.loads(Path(args.file).read_text())
        url = f"/workout-service/workout/{args.id}"
        resp = api.client.request("PUT", "connectapi", url, json=payload)
        status = getattr(resp, "status_code", None)
        if status is not None and status >= 300:
            body = getattr(resp, "text", "")
            print(f"ERROR: PUT returned {status}: {body}", file=sys.stderr)
            return 3
        # Garmin's PUT response varies — fall back to a fetch for the
        # canonical post-update state.
        try:
            updated = api.get_workout_by_id(args.id)
        except Exception:
            updated = {"updated": args.id}
        _output(updated, args.pretty)
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
