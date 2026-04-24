from __future__ import annotations

from unittest.mock import MagicMock, patch

from garmin_connect_cli.cli import main


def _run(argv, mock_api):
    with patch("garmin_connect_cli.client.login", return_value=mock_api):
        return main(argv)


class TestHealth:
    def test_sleep_calls_api(self, capsys):
        api = MagicMock()
        api.get_sleep_data.return_value = {"totalSleep": 7.5}
        rc = _run(["health", "sleep", "2026-04-24"], api)
        assert rc == 0
        api.get_sleep_data.assert_called_once_with("2026-04-24")

    def test_body_battery_range(self):
        api = MagicMock()
        api.get_body_battery.return_value = []
        rc = _run(["health", "body-battery", "2026-04-01", "2026-04-24"], api)
        assert rc == 0
        api.get_body_battery.assert_called_once_with("2026-04-01", "2026-04-24")

    def test_lactate_threshold(self):
        api = MagicMock()
        api.get_lactate_threshold.return_value = {}
        rc = _run(["health", "lactate-threshold"], api)
        assert rc == 0
        api.get_lactate_threshold.assert_called_once_with()


class TestStats:
    def test_progress(self):
        api = MagicMock()
        api.get_progress_summary_between_dates.return_value = []
        rc = _run(
            [
                "stats",
                "progress",
                "2026-01-01",
                "2026-04-24",
                "--metric",
                "duration",
            ],
            api,
        )
        assert rc == 0
        api.get_progress_summary_between_dates.assert_called_once_with(
            "2026-01-01", "2026-04-24", "duration", True
        )

    def test_badges_earned(self):
        api = MagicMock()
        api.get_earned_badges.return_value = []
        rc = _run(["stats", "badges", "--earned"], api)
        assert rc == 0
        api.get_earned_badges.assert_called_once()
        api.get_available_badges.assert_not_called()

    def test_challenges_virtual(self):
        api = MagicMock()
        api.get_inprogress_virtual_challenges.return_value = []
        rc = _run(["stats", "challenges", "virtual-inprogress"], api)
        assert rc == 0
        api.get_inprogress_virtual_challenges.assert_called_once_with(1, 50)


class TestActivities:
    def test_download_writes_file(self, tmp_path):
        api = MagicMock()
        api.download_activity.return_value = b"<tcx/>"
        out = tmp_path / "out.tcx"
        rc = _run(
            [
                "activities",
                "download",
                "99",
                "--format",
                "TCX",
                "--out",
                str(out),
            ],
            api,
        )
        assert rc == 0
        assert out.read_bytes() == b"<tcx/>"

    def test_typed_splits(self):
        api = MagicMock()
        api.get_activity_typed_splits.return_value = []
        rc = _run(["activities", "typed-splits", "42"], api)
        assert rc == 0
        api.get_activity_typed_splits.assert_called_once_with(42)

    def test_add_gear(self, capsys):
        api = MagicMock()
        rc = _run(["activities", "add-gear", "42", "gear-uuid"], api)
        assert rc == 0
        api.add_gear_to_activity.assert_called_once_with("gear-uuid", 42)


class TestGear:
    def test_list_resolves_profile(self):
        api = MagicMock()
        api.get_user_profile.return_value = {"userProfileNumber": 123}
        api.get_gear.return_value = []
        rc = _run(["gear", "list"], api)
        assert rc == 0
        api.get_gear.assert_called_once_with(123)

    def test_stats_uses_uuid(self):
        api = MagicMock()
        api.get_gear_stats.return_value = {}
        rc = _run(["gear", "stats", "abc-uuid"], api)
        assert rc == 0
        api.get_gear_stats.assert_called_once_with("abc-uuid")


class TestDevices:
    def test_list(self):
        api = MagicMock()
        api.get_devices.return_value = []
        rc = _run(["devices", "list"], api)
        assert rc == 0
        api.get_devices.assert_called_once()


class TestPlansGoalsUser:
    def test_plans_list(self):
        api = MagicMock()
        api.get_training_plans.return_value = []
        rc = _run(["plans", "list"], api)
        assert rc == 0
        api.get_training_plans.assert_called_once()

    def test_goals_list_default_active(self):
        api = MagicMock()
        api.get_goals.return_value = []
        rc = _run(["goals", "list"], api)
        assert rc == 0
        api.get_goals.assert_called_once_with("active", 0, 30)

    def test_user_profile(self):
        api = MagicMock()
        api.get_user_profile.return_value = {}
        rc = _run(["user", "profile"], api)
        assert rc == 0
        api.get_user_profile.assert_called_once()


class TestWorkoutsDownload:
    def test_download_writes_file(self, tmp_path):
        api = MagicMock()
        api.download_workout.return_value = b"FIT"
        out = tmp_path / "wo.fit"
        rc = _run(
            ["workouts", "download", "42", "--out", str(out)],
            api,
        )
        assert rc == 0
        assert out.read_bytes() == b"FIT"
