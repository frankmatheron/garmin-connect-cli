from __future__ import annotations

import argparse
import sys


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="garmin", description="Garmin Connect CLI")
    parser.add_argument(
        "-p", "--pretty", action="store_true", help="human-readable table output"
    )
    sub = parser.add_subparsers(dest="group")

    # -- login / logout --
    sub.add_parser("login", help="authenticate and cache tokens")
    sub.add_parser("logout", help="delete cached tokens")

    # -- workouts --
    wo = sub.add_parser("workouts")
    wo_sub = wo.add_subparsers(dest="command")

    wo_sub.add_parser("list")

    wo_get = wo_sub.add_parser("get")
    wo_get.add_argument("id", type=int)

    wo_create = wo_sub.add_parser("create")
    wo_create.add_argument("files", nargs="+")

    wo_del = wo_sub.add_parser("delete")
    wo_del.add_argument("id", type=int)

    # -- calendar --
    cal = sub.add_parser("calendar")
    cal_sub = cal.add_subparsers(dest="command")

    cal_list = cal_sub.add_parser("list")
    cal_list.add_argument("year", type=int)
    cal_list.add_argument("month", type=int)

    cal_add = cal_sub.add_parser("add")
    cal_add.add_argument("workout_id", type=int)
    cal_add.add_argument("date")

    cal_rm = cal_sub.add_parser("remove")
    cal_rm.add_argument("scheduled_id", type=int)

    # -- activities --
    act = sub.add_parser("activities")
    act_sub = act.add_subparsers(dest="command")

    act_list = act_sub.add_parser("list")
    act_list.add_argument("start", help="start date YYYY-MM-DD")
    act_list.add_argument("end", help="end date YYYY-MM-DD")
    act_list.add_argument("--type", default=None, help="activity type filter (e.g. running, cycling)")

    act_get = act_sub.add_parser("get")
    act_get.add_argument("id", type=int)

    act_splits = act_sub.add_parser("splits")
    act_splits.add_argument("id", type=int)

    act_details = act_sub.add_parser("details")
    act_details.add_argument("id", type=int)

    act_hr = act_sub.add_parser("hr")
    act_hr.add_argument("id", type=int)

    act_rename = act_sub.add_parser("rename")
    act_rename.add_argument("id", type=int)
    act_rename.add_argument("name")

    act_retype = act_sub.add_parser("retype")
    act_retype.add_argument("id", type=int)
    act_retype.add_argument("--type-id", type=int, default=1)
    act_retype.add_argument("--type-key", default="running")
    act_retype.add_argument("--parent-type-id", type=int, default=17)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.group:
        parser.print_help()
        return 1

    # login/logout don't need an authenticated API session
    if args.group == "login":
        from garmin_connect_cli.commands.auth import run_login

        return run_login(args)
    if args.group == "logout":
        from garmin_connect_cli.commands.auth import run_logout

        return run_logout(args)

    if not args.command:
        parser.print_help()
        return 1

    from garmin_connect_cli.client import login

    api = login()

    if args.group == "workouts":
        from garmin_connect_cli.commands.workouts import run
    elif args.group == "calendar":
        from garmin_connect_cli.commands.calendar import run
    elif args.group == "activities":
        from garmin_connect_cli.commands.activities import run
    else:
        parser.print_help()
        return 1

    from garminconnect import (
        GarminConnectConnectionError,
        GarminConnectTooManyRequestsError,
    )

    try:
        return run(api, args)
    except (GarminConnectConnectionError, GarminConnectTooManyRequestsError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 3
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    sys.exit(main())
