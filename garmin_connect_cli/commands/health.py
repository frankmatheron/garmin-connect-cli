from __future__ import annotations

import sys

from ._output import emit


def run(api, args) -> int:
    cmd = args.command
    p = args.pretty

    if cmd == "stats":
        emit(api.get_stats(args.date), p)
        return 0
    if cmd == "user-summary":
        emit(api.get_user_summary(args.date), p)
        return 0
    if cmd == "sleep":
        emit(api.get_sleep_data(args.date), p)
        return 0
    if cmd == "hrv":
        emit(api.get_hrv_data(args.date), p)
        return 0
    if cmd == "stress":
        emit(api.get_stress_data(args.date), p)
        return 0
    if cmd == "all-day-stress":
        emit(api.get_all_day_stress(args.date), p)
        return 0
    if cmd == "body-battery":
        emit(api.get_body_battery(args.start, args.end), p)
        return 0
    if cmd == "body-battery-events":
        emit(api.get_body_battery_events(args.date), p)
        return 0
    if cmd == "rhr":
        emit(api.get_rhr_day(args.date), p)
        return 0
    if cmd == "heart-rates":
        emit(api.get_heart_rates(args.date), p)
        return 0
    if cmd == "spo2":
        emit(api.get_spo2_data(args.date), p)
        return 0
    if cmd == "respiration":
        emit(api.get_respiration_data(args.date), p)
        return 0
    if cmd == "steps":
        emit(api.get_steps_data(args.date), p)
        return 0
    if cmd == "floors":
        emit(api.get_floors(args.date), p)
        return 0
    if cmd == "intensity":
        emit(api.get_intensity_minutes_data(args.date), p)
        return 0
    if cmd == "hydration":
        emit(api.get_hydration_data(args.date), p)
        return 0
    if cmd == "blood-pressure":
        emit(api.get_blood_pressure(args.start, args.end), p)
        return 0
    if cmd == "weight":
        emit(api.get_weigh_ins(args.start, args.end), p)
        return 0
    if cmd == "weight-day":
        emit(api.get_daily_weigh_ins(args.date), p)
        return 0
    if cmd == "body-comp":
        emit(api.get_body_composition(args.start, args.end), p)
        return 0
    if cmd == "stats-body":
        emit(api.get_stats_and_body(args.date), p)
        return 0
    if cmd == "max-metrics":
        emit(api.get_max_metrics(args.date), p)
        return 0
    if cmd == "lactate-threshold":
        emit(api.get_lactate_threshold(), p)
        return 0
    if cmd == "training-readiness":
        emit(api.get_training_readiness(args.date), p)
        return 0
    if cmd == "morning-readiness":
        emit(api.get_morning_training_readiness(args.date), p)
        return 0
    if cmd == "all-day-events":
        emit(api.get_all_day_events(args.date), p)
        return 0

    print(f"unknown health command: {cmd}", file=sys.stderr)
    return 1
