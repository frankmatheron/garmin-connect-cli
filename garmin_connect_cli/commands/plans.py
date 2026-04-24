from __future__ import annotations

import sys

from ._output import emit


def run(api, args) -> int:
    cmd = args.command
    p = args.pretty

    if cmd == "list":
        emit(api.get_training_plans(), p)
        return 0
    if cmd == "get":
        emit(api.get_training_plan_by_id(args.id), p)
        return 0
    if cmd == "get-adaptive":
        emit(api.get_adaptive_training_plan_by_id(args.id), p)
        return 0

    print(f"unknown plans command: {cmd}", file=sys.stderr)
    return 1
