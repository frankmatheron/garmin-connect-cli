from __future__ import annotations

import sys

from ._output import emit


def run(api, args) -> int:
    cmd = args.command
    p = args.pretty

    if cmd == "list":
        emit(api.get_goals(args.status, args.offset, args.limit), p)
        return 0

    print(f"unknown goals command: {cmd}", file=sys.stderr)
    return 1
