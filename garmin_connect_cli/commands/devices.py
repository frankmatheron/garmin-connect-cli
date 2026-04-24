from __future__ import annotations

import sys

from ._output import emit


def run(api, args) -> int:
    cmd = args.command
    p = args.pretty

    if cmd == "list":
        emit(api.get_devices(), p)
        return 0
    if cmd == "settings":
        emit(api.get_device_settings(args.device_id), p)
        return 0
    if cmd == "primary":
        emit(api.get_primary_training_device(), p)
        return 0
    if cmd == "alarms":
        emit(api.get_device_alarms(), p)
        return 0
    if cmd == "last-used":
        emit(api.get_device_last_used(), p)
        return 0
    if cmd == "solar":
        emit(
            api.get_device_solar_data(args.device_id, args.start, args.end),
            p,
        )
        return 0

    print(f"unknown devices command: {cmd}", file=sys.stderr)
    return 1
