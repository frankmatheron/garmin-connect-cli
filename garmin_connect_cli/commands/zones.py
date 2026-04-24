from __future__ import annotations

import json
import sys


ZONES_PATH = "/biometric-service/heartRateZones"

# Standard zone floor percentages for Karvonen (%HRR) and %Max.
# Applied as floor_N = base + pct * range, where:
#   HR_RESERVE: base = RHR, range = max - RHR
#   PERCENT_MAX_HR: base = 0, range = max
STANDARD_PERCENTS = (0.50, 0.60, 0.70, 0.80, 0.90)


def _compute_floors(method: str, max_hr: int, rhr: int) -> list[int]:
    if method == "HR_RESERVE":
        base, span = rhr, max_hr - rhr
    elif method == "PERCENT_MAX_HR":
        base, span = 0, max_hr
    else:
        raise ValueError(
            f"unsupported method: {method} (expected HR_RESERVE or PERCENT_MAX_HR)"
        )
    return [int(round(base + pct * span)) for pct in STANDARD_PERCENTS]


def _output(data: object, pretty: bool) -> None:
    if pretty and isinstance(data, list):
        print(f"{'sport':<10} {'method':<14} {'max':>4} {'rhr':>4}  "
              f"{'Z1':>4} {'Z2':>4} {'Z3':>4} {'Z4':>4} {'Z5':>4}")
        for entry in data:
            print(
                f"{entry.get('sport','?'):<10} "
                f"{entry.get('trainingMethod','?'):<14} "
                f"{entry.get('maxHeartRateUsed','?'):>4} "
                f"{entry.get('restingHeartRateUsed','?'):>4}  "
                f"{entry.get('zone1Floor','?'):>4} "
                f"{entry.get('zone2Floor','?'):>4} "
                f"{entry.get('zone3Floor','?'):>4} "
                f"{entry.get('zone4Floor','?'):>4} "
                f"{entry.get('zone5Floor','?'):>4}"
            )
    else:
        print(json.dumps(data, ensure_ascii=False))


def run(api, args) -> int:
    cmd = args.command

    if cmd == "list":
        data = api.connectapi(ZONES_PATH)
        _output(data, args.pretty)
        return 0

    if cmd == "set":
        method = args.method
        floors = (
            [int(x) for x in args.zones.split(",")]
            if args.zones
            else _compute_floors(method, args.max_hr, args.rhr)
        )
        if len(floors) != 5:
            print(
                "ERROR: --zones must be 5 comma-separated integers (Z1..Z5 floors)",
                file=sys.stderr,
            )
            return 2

        sports_arg = [s.strip().upper() for s in args.sport.split(",")]
        current = api.connectapi(ZONES_PATH)
        payload = []
        updated_sports: list[str] = []
        for entry in current:
            if entry.get("sport") in sports_arg:
                payload.append({
                    **entry,
                    "trainingMethod": method,
                    "maxHeartRateUsed": args.max_hr,
                    "restingHeartRateUsed": args.rhr,
                    "zone1Floor": floors[0],
                    "zone2Floor": floors[1],
                    "zone3Floor": floors[2],
                    "zone4Floor": floors[3],
                    "zone5Floor": floors[4],
                    "changeState": "CHANGED",
                })
                updated_sports.append(entry["sport"])
            else:
                payload.append(entry)

        missing = [s for s in sports_arg if s not in updated_sports]
        if missing:
            print(
                f"WARNING: no existing zone entry for sport(s): {','.join(missing)}",
                file=sys.stderr,
            )

        resp = api.client.request("PUT", "connectapi", ZONES_PATH, json=payload)
        status = getattr(resp, "status_code", None)
        if status is not None and status >= 300:
            body = getattr(resp, "text", "")
            print(f"ERROR: PUT returned {status}: {body}", file=sys.stderr)
            return 3

        after = api.connectapi(ZONES_PATH)
        _output(after, args.pretty)
        return 0

    print(f"unknown zones command: {cmd}", file=sys.stderr)
    return 1
