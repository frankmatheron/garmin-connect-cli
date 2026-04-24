from __future__ import annotations

import sys

from ._output import emit


def run(api, args) -> int:
    cmd = args.command
    p = args.pretty

    if cmd == "progress":
        emit(
            api.get_progress_summary_between_dates(
                args.start, args.end, args.metric, args.group_by_activities
            ),
            p,
        )
        return 0
    if cmd == "daily-steps":
        emit(api.get_daily_steps(args.start, args.end), p)
        return 0
    if cmd == "weekly-steps":
        emit(api.get_weekly_steps(args.end, args.weeks), p)
        return 0
    if cmd == "weekly-stress":
        emit(api.get_weekly_stress(args.end, args.weeks), p)
        return 0
    if cmd == "weekly-intensity":
        emit(api.get_weekly_intensity_minutes(args.start, args.end), p)
        return 0
    if cmd == "training-status":
        emit(api.get_training_status(args.date), p)
        return 0
    if cmd == "fitness-age":
        emit(api.get_fitnessage_data(args.date), p)
        return 0
    if cmd == "endurance":
        emit(api.get_endurance_score(args.start, args.end), p)
        return 0
    if cmd == "hill-score":
        emit(api.get_hill_score(args.start, args.end), p)
        return 0
    if cmd == "race-predictions":
        emit(api.get_race_predictions(args.start, args.end, args.type), p)
        return 0
    if cmd == "running-tolerance":
        emit(
            api.get_running_tolerance(args.start, args.end, args.aggregation),
            p,
        )
        return 0
    if cmd == "personal-records":
        emit(api.get_personal_record(), p)
        return 0
    if cmd == "badges":
        if args.earned:
            emit(api.get_earned_badges(), p)
        elif args.available:
            emit(api.get_available_badges(), p)
        elif args.in_progress:
            emit(api.get_in_progress_badges(), p)
        else:
            emit(
                {
                    "earned": api.get_earned_badges(),
                    "in_progress": api.get_in_progress_badges(),
                },
                p,
            )
        return 0
    if cmd == "challenges":
        kind = args.kind
        if kind == "adhoc":
            emit(api.get_adhoc_challenges(args.start, args.limit), p)
        elif kind == "badge":
            emit(api.get_badge_challenges(args.start, args.limit), p)
        elif kind == "available":
            emit(api.get_available_badge_challenges(args.start, args.limit), p)
        elif kind == "non-completed":
            emit(api.get_non_completed_badge_challenges(args.start, args.limit), p)
        elif kind == "virtual-inprogress":
            emit(api.get_inprogress_virtual_challenges(args.start, args.limit), p)
        else:
            print(f"unknown challenge kind: {kind}", file=sys.stderr)
            return 1
        return 0

    print(f"unknown stats command: {cmd}", file=sys.stderr)
    return 1
