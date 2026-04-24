from __future__ import annotations

import argparse
import sys


ROOT_EPILOG = """\
Output
  JSON by default. `-p` / `--pretty` produces a table for list responses
  and indented JSON for objects.

Exit codes
  0 success · 1 usage error · 2 auth error · 3 API / rate-limit error

Authentication
  login                  authenticate and cache tokens under
                         $XDG_DATA_HOME/garmin-connect-cli/tokens/
  logout                 delete cached tokens

Command groups
  activities             list, inspect, rename, retype, download, upload,
                         delete activities; attach gear; weather; splits
  workouts               list/get/create/delete/download structured workouts
  calendar               list/add/remove scheduled workout instances
  zones                  read and write HR zone configuration per sport
  health                 daily health metrics (sleep, HRV, stress, RHR,
                         body battery, SpO2, weight, readiness, …)
  stats                  progress, weekly rollups, training status, race
                         predictions, running tolerance, records, badges
  gear                   list/inspect gear, set gear defaults per sport
  devices                devices, device settings, alarms, solar data
  goals                  list goals
  plans                  list/inspect training plans (incl. adaptive)
  user                   profile, settings, display name, unit system

Dates are ISO YYYY-MM-DD unless stated otherwise.

Use `garmin <group> --help` for a list of subcommands and
`garmin <group> <cmd> --help` for the arguments of a specific command.
"""


def _add_date(parser: argparse.ArgumentParser, *, name: str = "date", help: str = "date YYYY-MM-DD") -> None:
    parser.add_argument(name, help=help)


def _add_range(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("start", help="start date YYYY-MM-DD")
    parser.add_argument("end", help="end date YYYY-MM-DD")


def _build_workouts(sub: argparse._SubParsersAction) -> None:
    wo = sub.add_parser(
        "workouts",
        help="structured workout library",
        description="Manage the structured workout library on Garmin Connect.",
    )
    wo_sub = wo.add_subparsers(dest="command", metavar="<command>")

    wo_sub.add_parser("list", help="list all saved workouts")

    p = wo_sub.add_parser("get", help="fetch one workout by id")
    p.add_argument("id", type=int)

    p = wo_sub.add_parser(
        "create",
        help="upload one or more workout JSON files",
        description=(
            "Upload one or more workout JSON files to Garmin Connect. "
            "Use `-` to read a single payload from stdin."
        ),
        epilog="Example:\n  garmin workouts create my-workout.json\n  cat plan.json | garmin workouts create -",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("files", nargs="+", help="path(s) to workout JSON, or `-` for stdin")

    p = wo_sub.add_parser("delete", help="delete a workout by id")
    p.add_argument("id", type=int)

    p = wo_sub.add_parser(
        "download",
        help="download a workout as FIT",
        description="Download a workout's FIT file to disk.",
    )
    p.add_argument("id", type=int)
    p.add_argument("--out", default=None, help="output path (default: workout_<id>.fit)")


def _build_calendar(sub: argparse._SubParsersAction) -> None:
    cal = sub.add_parser(
        "calendar",
        help="scheduled workouts",
        description="Schedule and unschedule structured workouts on specific dates.",
    )
    cal_sub = cal.add_subparsers(dest="command", metavar="<command>")

    p = cal_sub.add_parser("list", help="list scheduled workouts for a given month")
    p.add_argument("year", type=int)
    p.add_argument("month", type=int, help="1-12")

    p = cal_sub.add_parser("add", help="schedule a workout on a date")
    p.add_argument("workout_id", type=int)
    p.add_argument("date", help="YYYY-MM-DD")

    p = cal_sub.add_parser("remove", help="unschedule by scheduledWorkoutId")
    p.add_argument("scheduled_id", type=int)


def _build_activities(sub: argparse._SubParsersAction) -> None:
    act = sub.add_parser(
        "activities",
        help="recorded activities",
        description="List, inspect, classify, upload, download and delete recorded activities.",
    )
    act_sub = act.add_subparsers(dest="command", metavar="<command>")

    p = act_sub.add_parser(
        "list",
        help="list activities in a date range",
        description="List activities between two dates (inclusive).",
    )
    p.add_argument("start", help="start date YYYY-MM-DD")
    p.add_argument("end", help="end date YYYY-MM-DD")
    p.add_argument("--type", default=None, help="activity type filter (e.g. running, cycling)")

    p = act_sub.add_parser(
        "recent",
        help="list most recent N activities",
        description="Paginated listing of recent activities.",
    )
    p.add_argument("--offset", type=int, default=0)
    p.add_argument("--limit", type=int, default=20)
    p.add_argument("--type", default=None, help="activity type filter")

    act_sub.add_parser("count", help="total activity count")
    act_sub.add_parser("types", help="activity type catalog")
    act_sub.add_parser("last", help="most recent single activity")

    p = act_sub.add_parser("fordate", help="activities recorded on a given date")
    _add_date(p)

    p = act_sub.add_parser("get", help="fetch one activity by id")
    p.add_argument("id", type=int)

    p = act_sub.add_parser("splits", help="lap splits for an activity")
    p.add_argument("id", type=int)

    p = act_sub.add_parser("typed-splits", help="typed (interval/recovery/rest) splits")
    p.add_argument("id", type=int)

    p = act_sub.add_parser("split-summaries", help="aggregated split summaries")
    p.add_argument("id", type=int)

    p = act_sub.add_parser("details", help="full activity details (charts + polyline)")
    p.add_argument("id", type=int)
    p.add_argument("--max-chart", type=int, default=2000, dest="max_chart")
    p.add_argument("--max-poly", type=int, default=4000, dest="max_poly")

    p = act_sub.add_parser("hr", help="time-in-HR-zone breakdown")
    p.add_argument("id", type=int)

    p = act_sub.add_parser("power", help="time-in-power-zone breakdown (cycling)")
    p.add_argument("id", type=int)

    p = act_sub.add_parser("weather", help="weather snapshot for an activity")
    p.add_argument("id", type=int)

    p = act_sub.add_parser("exercise-sets", help="strength exercise sets")
    p.add_argument("id", type=int)

    p = act_sub.add_parser("gear", help="gear attached to an activity")
    p.add_argument("id", type=int)

    p = act_sub.add_parser("add-gear", help="attach a gear item to an activity")
    p.add_argument("id", type=int)
    p.add_argument("gear_uuid", help="gear UUID (see `garmin gear list`)")

    p = act_sub.add_parser("remove-gear", help="detach a gear item from an activity")
    p.add_argument("id", type=int)
    p.add_argument("gear_uuid")

    p = act_sub.add_parser("rename", help="change an activity's display name")
    p.add_argument("id", type=int)
    p.add_argument("name", help="new name (quote if it has spaces)")

    p = act_sub.add_parser(
        "retype",
        help="change an activity's type classification",
        description=(
            "Reclassify an activity. Common mappings: running type-id=1 "
            "parent=17, cycling type-id=2 parent=17, walking type-id=9 "
            "parent=17, strength type-id=13 parent=29."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("id", type=int)
    p.add_argument("--type-id", type=int, default=1)
    p.add_argument("--type-key", default="running")
    p.add_argument("--parent-type-id", type=int, default=17)

    p = act_sub.add_parser(
        "download",
        help="download activity file (TCX/GPX/KML/CSV/original)",
        description="Download an activity in the requested format.",
    )
    p.add_argument("id", type=int)
    p.add_argument(
        "--format",
        default="TCX",
        choices=["ORIGINAL", "TCX", "GPX", "KML", "CSV"],
        help="download format (default: TCX; ORIGINAL returns the FIT zip)",
    )
    p.add_argument("--out", default=None, help="output path (default: activity_<id>.<ext>)")

    p = act_sub.add_parser("upload", help="upload a FIT/GPX/TCX file as a new activity")
    p.add_argument("file", help="path to FIT/GPX/TCX")

    p = act_sub.add_parser("import", help="same as upload (library alias)")
    p.add_argument("file")

    p = act_sub.add_parser("delete", help="delete an activity")
    p.add_argument("id", type=int)

    p = act_sub.add_parser(
        "manual-create",
        help="create a manual activity entry",
        description="Log an activity by hand without a recorded file.",
    )
    p.add_argument("start_datetime", help="ISO 8601 local start, e.g. 2026-04-24T07:30:00")
    p.add_argument("timezone", help="IANA tz, e.g. Europe/Amsterdam")
    p.add_argument("type_key", help="e.g. running, cycling, walking")
    p.add_argument("distance_km", type=float)
    p.add_argument("duration_min", type=float)
    p.add_argument("name")


def _build_zones(sub: argparse._SubParsersAction) -> None:
    zn = sub.add_parser(
        "zones",
        help="HR zone configuration per sport",
        description=(
            "Read and write HR zone configuration. Zones are stored per "
            "sport (DEFAULT plus optional overrides like RUNNING). "
            "Structured workouts targeting heart.rate.zone resolve against "
            "the sport-specific set if present, else DEFAULT — a desynced "
            "RUNNING override silently drifts workout targets away from "
            "the profile values shown in the web UI."
        ),
        epilog=(
            "Examples:\n"
            "  garmin zones list\n"
            "  garmin -p zones list\n"
            "  garmin zones set --max-hr 190 --rhr 47\n"
            "  garmin zones set --max-hr 190 --rhr 47 --sport RUNNING\n"
            "  garmin zones set --max-hr 190 --rhr 47 --method PERCENT_MAX_HR\n"
            "  garmin zones set --max-hr 190 --rhr 47 --zones 118,133,147,161,176"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    zn_sub = zn.add_subparsers(dest="command", metavar="<command>")

    zn_sub.add_parser("list", help="show current HR zones per sport")

    p = zn_sub.add_parser(
        "set",
        help="set max HR, resting HR, and zone floors (DEFAULT+RUNNING by default)",
    )
    p.add_argument("--max-hr", type=int, required=True, dest="max_hr")
    p.add_argument("--rhr", type=int, required=True)
    p.add_argument(
        "--method",
        default="HR_RESERVE",
        choices=["HR_RESERVE", "PERCENT_MAX_HR"],
        help="zone calculation method (default: HR_RESERVE / Karvonen)",
    )
    p.add_argument(
        "--sport",
        default="DEFAULT,RUNNING",
        help="comma-separated sports to update (default: DEFAULT,RUNNING)",
    )
    p.add_argument(
        "--zones",
        default=None,
        help="override zone floors as Z1,Z2,Z3,Z4,Z5 (default: auto 50/60/70/80/90%%)",
    )


def _build_health(sub: argparse._SubParsersAction) -> None:
    h = sub.add_parser(
        "health",
        help="daily health metrics",
        description=(
            "Daily health and physiology metrics. Most subcommands take a "
            "single date; a few take a start/end range."
        ),
    )
    h_sub = h.add_subparsers(dest="command", metavar="<command>")

    # single-date subcommands
    for name, helpstr in [
        ("stats", "overall daily stats summary"),
        ("user-summary", "user daily summary"),
        ("sleep", "sleep data for a date"),
        ("hrv", "overnight HRV"),
        ("stress", "stress time series"),
        ("all-day-stress", "all-day stress summary"),
        ("body-battery-events", "body-battery events for a date"),
        ("rhr", "resting heart rate for a date"),
        ("heart-rates", "HR time series for a date"),
        ("spo2", "pulse oximetry for a date"),
        ("respiration", "respiration rate for a date"),
        ("steps", "step data for a date"),
        ("floors", "floors climbed for a date"),
        ("intensity", "intensity minutes for a date"),
        ("hydration", "hydration log for a date"),
        ("weight-day", "weigh-ins for a date"),
        ("stats-body", "daily stats + body composition"),
        ("max-metrics", "VO2max and related max metrics"),
        ("training-readiness", "training readiness score"),
        ("morning-readiness", "morning training readiness"),
        ("all-day-events", "all-day events (moves, naps, etc.)"),
    ]:
        p = h_sub.add_parser(name, help=helpstr)
        _add_date(p)

    # ranged subcommands
    p = h_sub.add_parser("body-battery", help="body battery over a range")
    _add_range(p)

    p = h_sub.add_parser("blood-pressure", help="blood pressure over a range")
    _add_range(p)

    p = h_sub.add_parser("weight", help="weigh-ins over a range")
    _add_range(p)

    p = h_sub.add_parser("body-comp", help="body composition over a range")
    _add_range(p)

    # no-arg
    h_sub.add_parser("lactate-threshold", help="lactate threshold (no date arg)")


def _build_stats(sub: argparse._SubParsersAction) -> None:
    s = sub.add_parser(
        "stats",
        help="trends, progress, predictions",
        description="Progress summaries, weekly rollups, training status, and predictions.",
    )
    s_sub = s.add_subparsers(dest="command", metavar="<command>")

    p = s_sub.add_parser(
        "progress",
        help="activity progress summary between two dates",
        description="Aggregate activity totals/averages between two dates.",
    )
    _add_range(p)
    p.add_argument(
        "--metric",
        default="distance",
        help="metric to aggregate (e.g. distance, duration, elevationGain; default: distance)",
    )
    p.add_argument(
        "--group-by-activities",
        action="store_true",
        default=True,
        help="group totals by activity type (default: on)",
    )

    p = s_sub.add_parser("daily-steps", help="daily steps over a range")
    _add_range(p)

    p = s_sub.add_parser("weekly-steps", help="weekly steps ending on a date")
    p.add_argument("end", help="YYYY-MM-DD")
    p.add_argument("--weeks", type=int, default=52)

    p = s_sub.add_parser("weekly-stress", help="weekly stress ending on a date")
    p.add_argument("end", help="YYYY-MM-DD")
    p.add_argument("--weeks", type=int, default=52)

    p = s_sub.add_parser("weekly-intensity", help="weekly intensity minutes")
    _add_range(p)

    p = s_sub.add_parser("training-status", help="training status for a date")
    _add_date(p)

    p = s_sub.add_parser("fitness-age", help="fitness age for a date")
    _add_date(p)

    p = s_sub.add_parser("endurance", help="endurance score over a range")
    _add_range(p)

    p = s_sub.add_parser("hill-score", help="hill score over a range")
    _add_range(p)

    p = s_sub.add_parser(
        "race-predictions",
        help="race time predictions",
        description="Range + distance are optional; omit for the default window.",
    )
    p.add_argument("--start", default=None, help="YYYY-MM-DD")
    p.add_argument("--end", default=None, help="YYYY-MM-DD")
    p.add_argument("--type", default=None, help="distance filter (e.g. 5K, 10K)")

    p = s_sub.add_parser("running-tolerance", help="running tolerance (load capacity)")
    _add_range(p)
    p.add_argument(
        "--aggregation",
        default="weekly",
        choices=["daily", "weekly"],
        help="aggregation window (default: weekly)",
    )

    s_sub.add_parser("personal-records", help="all personal records")

    p = s_sub.add_parser(
        "badges",
        help="badges (earned / available / in-progress)",
        description="Without flags, returns both earned and in-progress.",
    )
    g = p.add_mutually_exclusive_group()
    g.add_argument("--earned", action="store_true")
    g.add_argument("--available", action="store_true")
    g.add_argument("--in-progress", action="store_true", dest="in_progress")

    p = s_sub.add_parser(
        "challenges",
        help="challenges: adhoc, badge, available, non-completed, virtual-inprogress",
    )
    p.add_argument(
        "kind",
        choices=["adhoc", "badge", "available", "non-completed", "virtual-inprogress"],
    )
    p.add_argument("--start", type=int, default=1)
    p.add_argument("--limit", type=int, default=50)


def _build_gear(sub: argparse._SubParsersAction) -> None:
    g = sub.add_parser(
        "gear",
        help="gear library and defaults",
        description=(
            "List gear, view per-gear stats and activities, and set gear "
            "defaults per activity type. Profile id is auto-resolved from "
            "the current user unless --profile-id is given."
        ),
    )
    g_sub = g.add_subparsers(dest="command", metavar="<command>")

    p = g_sub.add_parser("list", help="list all gear")
    p.add_argument("--profile-id", type=int, default=None, dest="profile_id")

    p = g_sub.add_parser("stats", help="stats for one gear item")
    p.add_argument("uuid", help="gear UUID")

    p = g_sub.add_parser("activities", help="activities recorded with one gear item")
    p.add_argument("uuid")
    p.add_argument("--limit", type=int, default=50)

    p = g_sub.add_parser("defaults", help="current gear defaults per activity type")
    p.add_argument("--profile-id", type=int, default=None, dest="profile_id")

    p = g_sub.add_parser(
        "set-default",
        help="set a gear item as default for an activity type",
    )
    p.add_argument("activity_type", type=int, help="activity type id (e.g. 1=running)")
    p.add_argument("uuid", help="gear UUID")
    p.add_argument("--no-default", action="store_false", dest="default", default=True,
                   help="clear rather than set as default")


def _build_devices(sub: argparse._SubParsersAction) -> None:
    d = sub.add_parser(
        "devices",
        help="registered devices and device data",
        description="Registered devices, device settings, alarms, and solar data.",
    )
    d_sub = d.add_subparsers(dest="command", metavar="<command>")

    d_sub.add_parser("list", help="list all registered devices")
    p = d_sub.add_parser("settings", help="settings for one device")
    p.add_argument("device_id", type=int)
    d_sub.add_parser("primary", help="primary training device")
    d_sub.add_parser("alarms", help="device alarms across devices")
    d_sub.add_parser("last-used", help="most recently used device")

    p = d_sub.add_parser("solar", help="solar charging data for a device over a range")
    p.add_argument("device_id", type=int)
    _add_range(p)


def _build_goals(sub: argparse._SubParsersAction) -> None:
    g = sub.add_parser(
        "goals",
        help="goals",
        description="List goals by status.",
    )
    g_sub = g.add_subparsers(dest="command", metavar="<command>")

    p = g_sub.add_parser("list", help="list goals")
    p.add_argument(
        "--status",
        default="active",
        choices=["active", "past", "future"],
        help="goal status filter (default: active)",
    )
    p.add_argument("--offset", type=int, default=0)
    p.add_argument("--limit", type=int, default=30)


def _build_plans(sub: argparse._SubParsersAction) -> None:
    pl = sub.add_parser(
        "plans",
        help="training plans",
        description="List and inspect training plans, including adaptive plans.",
    )
    pl_sub = pl.add_subparsers(dest="command", metavar="<command>")

    pl_sub.add_parser("list", help="list training plans")

    p = pl_sub.add_parser("get", help="fetch one training plan by id")
    p.add_argument("id", type=int)

    p = pl_sub.add_parser("get-adaptive", help="fetch an adaptive training plan by id")
    p.add_argument("id", type=int)


def _build_user(sub: argparse._SubParsersAction) -> None:
    u = sub.add_parser(
        "user",
        help="user profile and settings",
        description="User profile, user settings, display name, and unit system.",
    )
    u_sub = u.add_subparsers(dest="command", metavar="<command>")

    u_sub.add_parser("profile", help="full user profile")
    u_sub.add_parser("settings", help="user profile settings")
    u_sub.add_parser("name", help="display name only")
    u_sub.add_parser("units", help="unit system (metric/statute)")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="garmin",
        description="Garmin Connect CLI — inspect and manage your Garmin account.",
        epilog=ROOT_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-p", "--pretty", action="store_true", help="human-readable output"
    )
    sub = parser.add_subparsers(dest="group", metavar="<group>")

    sub.add_parser("login", help="authenticate and cache session tokens")
    sub.add_parser("logout", help="delete cached session tokens")

    _build_workouts(sub)
    _build_calendar(sub)
    _build_activities(sub)
    _build_zones(sub)
    _build_health(sub)
    _build_stats(sub)
    _build_gear(sub)
    _build_devices(sub)
    _build_goals(sub)
    _build_plans(sub)
    _build_user(sub)

    return parser


_RUN_MODULES = {
    "workouts": "garmin_connect_cli.commands.workouts",
    "calendar": "garmin_connect_cli.commands.calendar",
    "activities": "garmin_connect_cli.commands.activities",
    "zones": "garmin_connect_cli.commands.zones",
    "health": "garmin_connect_cli.commands.health",
    "stats": "garmin_connect_cli.commands.stats",
    "gear": "garmin_connect_cli.commands.gear",
    "devices": "garmin_connect_cli.commands.devices",
    "goals": "garmin_connect_cli.commands.goals",
    "plans": "garmin_connect_cli.commands.plans",
    "user": "garmin_connect_cli.commands.user",
}


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.group:
        parser.print_help()
        return 1

    if args.group == "login":
        from garmin_connect_cli.commands.auth import run_login
        return run_login(args)
    if args.group == "logout":
        from garmin_connect_cli.commands.auth import run_logout
        return run_logout(args)

    if not getattr(args, "command", None):
        parser.parse_args([args.group, "--help"])
        return 1

    module_name = _RUN_MODULES.get(args.group)
    if not module_name:
        parser.print_help()
        return 1

    from garmin_connect_cli.client import login

    api = login()

    import importlib

    mod = importlib.import_module(module_name)

    from garminconnect import (
        GarminConnectConnectionError,
        GarminConnectTooManyRequestsError,
    )

    try:
        return mod.run(api, args)
    except (GarminConnectConnectionError, GarminConnectTooManyRequestsError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 3
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    sys.exit(main())
