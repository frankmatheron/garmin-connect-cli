from __future__ import annotations

import sys

from ._output import emit


def run(api, args) -> int:
    cmd = args.command
    p = args.pretty

    if cmd == "profile":
        emit(api.get_user_profile(), p)
        return 0
    if cmd == "settings":
        emit(api.get_userprofile_settings(), p)
        return 0
    if cmd == "name":
        emit({"fullName": api.get_full_name()}, p)
        return 0
    if cmd == "units":
        emit({"unitSystem": api.get_unit_system()}, p)
        return 0

    print(f"unknown user command: {cmd}", file=sys.stderr)
    return 1
