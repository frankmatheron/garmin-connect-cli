from __future__ import annotations

from garmin_connect_cli.cli import build_parser


class TestBuildParser:
    def test_workouts_list(self):
        parser = build_parser()
        args = parser.parse_args(["workouts", "list"])
        assert args.group == "workouts"
        assert args.command == "list"
        assert args.pretty is False

    def test_workouts_get(self):
        parser = build_parser()
        args = parser.parse_args(["workouts", "get", "12345"])
        assert args.command == "get"
        assert args.id == 12345

    def test_workouts_create_files(self):
        parser = build_parser()
        args = parser.parse_args(["workouts", "create", "a.json", "b.json"])
        assert args.command == "create"
        assert args.files == ["a.json", "b.json"]

    def test_workouts_create_stdin(self):
        parser = build_parser()
        args = parser.parse_args(["workouts", "create", "-"])
        assert args.files == ["-"]

    def test_workouts_delete(self):
        parser = build_parser()
        args = parser.parse_args(["workouts", "delete", "12345"])
        assert args.command == "delete"
        assert args.id == 12345

    def test_calendar_list(self):
        parser = build_parser()
        args = parser.parse_args(["calendar", "list", "2026", "4"])
        assert args.group == "calendar"
        assert args.command == "list"
        assert args.year == 2026
        assert args.month == 4

    def test_calendar_add(self):
        parser = build_parser()
        args = parser.parse_args(["calendar", "add", "999", "2026-04-17"])
        assert args.command == "add"
        assert args.workout_id == 999
        assert args.date == "2026-04-17"

    def test_calendar_remove(self):
        parser = build_parser()
        args = parser.parse_args(["calendar", "remove", "555"])
        assert args.command == "remove"
        assert args.scheduled_id == 555

    def test_pretty_flag(self):
        parser = build_parser()
        args = parser.parse_args(["-p", "workouts", "list"])
        assert args.pretty is True
        args2 = parser.parse_args(["--pretty", "workouts", "list"])
        assert args2.pretty is True

    def test_login_subcommand(self):
        parser = build_parser()
        args = parser.parse_args(["login"])
        assert args.group == "login"

    def test_logout_subcommand(self):
        parser = build_parser()
        args = parser.parse_args(["logout"])
        assert args.group == "logout"


class TestNewCommandGroups:
    def test_health_sleep(self):
        args = build_parser().parse_args(["health", "sleep", "2026-04-24"])
        assert args.group == "health"
        assert args.command == "sleep"
        assert args.date == "2026-04-24"

    def test_health_body_battery_range(self):
        args = build_parser().parse_args(
            ["health", "body-battery", "2026-04-01", "2026-04-24"]
        )
        assert args.command == "body-battery"
        assert args.start == "2026-04-01"
        assert args.end == "2026-04-24"

    def test_stats_progress_defaults(self):
        args = build_parser().parse_args(
            ["stats", "progress", "2026-01-01", "2026-04-24"]
        )
        assert args.metric == "distance"
        assert args.group_by_activities is True

    def test_stats_weekly_steps(self):
        args = build_parser().parse_args(
            ["stats", "weekly-steps", "2026-04-24", "--weeks", "8"]
        )
        assert args.end == "2026-04-24"
        assert args.weeks == 8

    def test_stats_badges_mutex(self):
        args = build_parser().parse_args(["stats", "badges", "--earned"])
        assert args.earned is True
        assert args.available is False

    def test_stats_challenges(self):
        args = build_parser().parse_args(["stats", "challenges", "adhoc"])
        assert args.kind == "adhoc"
        assert args.start == 1

    def test_activities_download_format(self):
        args = build_parser().parse_args(
            ["activities", "download", "12345", "--format", "GPX"]
        )
        assert args.id == 12345
        assert args.format == "GPX"

    def test_activities_typed_splits(self):
        args = build_parser().parse_args(["activities", "typed-splits", "12345"])
        assert args.command == "typed-splits"

    def test_gear_set_default(self):
        args = build_parser().parse_args(
            ["gear", "set-default", "1", "abc-uuid"]
        )
        assert args.activity_type == 1
        assert args.uuid == "abc-uuid"
        assert args.default is True

    def test_devices_solar(self):
        args = build_parser().parse_args(
            ["devices", "solar", "42", "2026-04-01", "2026-04-24"]
        )
        assert args.device_id == 42

    def test_goals_list_defaults(self):
        args = build_parser().parse_args(["goals", "list"])
        assert args.status == "active"
        assert args.limit == 30

    def test_plans_get(self):
        args = build_parser().parse_args(["plans", "get", "777"])
        assert args.command == "get"
        assert args.id == 777

    def test_user_profile(self):
        args = build_parser().parse_args(["user", "profile"])
        assert args.group == "user"
        assert args.command == "profile"

    def test_workouts_download(self):
        args = build_parser().parse_args(["workouts", "download", "42"])
        assert args.command == "download"
        assert args.id == 42


class TestMainErrorHandling:
    def test_api_error_returns_exit_3(self, monkeypatch, capsys):
        """API errors during command execution should exit 3."""
        from unittest.mock import patch, MagicMock
        from garminconnect import GarminConnectTooManyRequestsError

        from garmin_connect_cli.cli import main

        mock_api = MagicMock()
        mock_api.get_workouts.side_effect = GarminConnectTooManyRequestsError("rate limited")
        with patch("garmin_connect_cli.client.login", return_value=mock_api):
            rc = main(["workouts", "list"])
        assert rc == 3
        assert "rate limited" in capsys.readouterr().err
