from __future__ import annotations

import sys

from ._output import emit


def _resolve_profile_id(api, explicit: int | None) -> int:
    if explicit is not None:
        return explicit
    profile = api.get_user_profile()
    for key in ("userProfileNumber", "userProfileId", "id"):
        if isinstance(profile, dict) and profile.get(key):
            return int(profile[key])
    raise RuntimeError("could not resolve user profile number; pass --profile-id")


def run(api, args) -> int:
    cmd = args.command
    p = args.pretty

    if cmd == "list":
        emit(api.get_gear(_resolve_profile_id(api, args.profile_id)), p)
        return 0
    if cmd == "stats":
        emit(api.get_gear_stats(args.uuid), p)
        return 0
    if cmd == "activities":
        emit(api.get_gear_activities(args.uuid, args.limit), p)
        return 0
    if cmd == "defaults":
        emit(api.get_gear_defaults(_resolve_profile_id(api, args.profile_id)), p)
        return 0
    if cmd == "set-default":
        api.set_gear_default(args.activity_type, args.uuid, args.default)
        print(f"set gear {args.uuid} as default for activityType={args.activity_type}")
        return 0

    print(f"unknown gear command: {cmd}", file=sys.stderr)
    return 1
