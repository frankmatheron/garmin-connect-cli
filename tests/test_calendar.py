from __future__ import annotations

import json
from types import SimpleNamespace

from garmin_connect_cli.commands.calendar import run


class TestCalendarList:
    def test_list_prints_json(self, mock_api, capsys):
        mock_api.get_scheduled_workouts.return_value = [
            {"scheduledWorkoutId": 1, "date": "2026-04-20"},
        ]
        args = SimpleNamespace(command="list", year=2026, month=4, pretty=False)
        rc = run(mock_api, args)
        assert rc == 0
        out = json.loads(capsys.readouterr().out)
        assert out[0]["scheduledWorkoutId"] == 1
        mock_api.get_scheduled_workouts.assert_called_once_with(2026, 4)


class TestCalendarAdd:
    def test_add(self, mock_api, capsys):
        mock_api.schedule_workout.return_value = {"scheduledWorkoutId": 77}
        args = SimpleNamespace(
            command="add", workout_id=999, date="2026-04-17", pretty=False
        )
        rc = run(mock_api, args)
        assert rc == 0
        mock_api.schedule_workout.assert_called_once_with(999, "2026-04-17")
        out = json.loads(capsys.readouterr().out)
        assert out["scheduledWorkoutId"] == 77


class TestCalendarRemove:
    def test_remove(self, mock_api, capsys):
        mock_api.unschedule_workout.return_value = None
        args = SimpleNamespace(command="remove", scheduled_id=555, pretty=False)
        rc = run(mock_api, args)
        assert rc == 0
        mock_api.unschedule_workout.assert_called_once_with(555)
