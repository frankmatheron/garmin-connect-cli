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
