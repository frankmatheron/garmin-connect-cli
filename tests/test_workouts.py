from __future__ import annotations

import json
from types import SimpleNamespace

from garmin_connect_cli.commands.workouts import run


class TestWorkoutsList:
    def test_list_prints_json(self, mock_api, capsys):
        mock_api.get_workouts.return_value = [
            {"workoutId": 1, "workoutName": "Test"},
            {"workoutId": 2, "workoutName": "Test 2"},
        ]
        args = SimpleNamespace(command="list", pretty=False)
        rc = run(mock_api, args)
        assert rc == 0
        out = json.loads(capsys.readouterr().out)
        assert len(out) == 2
        assert out[0]["workoutId"] == 1


class TestWorkoutsGet:
    def test_get_prints_json(self, mock_api, capsys):
        mock_api.get_workout_by_id.return_value = {
            "workoutId": 42,
            "workoutName": "Full detail",
            "workoutSegments": [],
        }
        args = SimpleNamespace(command="get", id=42, pretty=False)
        rc = run(mock_api, args)
        assert rc == 0
        out = json.loads(capsys.readouterr().out)
        assert out["workoutId"] == 42
        mock_api.get_workout_by_id.assert_called_once_with(42)


class TestWorkoutsCreate:
    def test_create_from_file(self, mock_api, capsys, tmp_path):
        payload = {"workoutName": "New", "sportType": {"sportTypeId": 1}}
        f = tmp_path / "w.json"
        f.write_text(json.dumps(payload))
        mock_api.upload_workout.return_value = {"workoutId": 99}
        args = SimpleNamespace(command="create", files=[str(f)], pretty=False)
        rc = run(mock_api, args)
        assert rc == 0
        mock_api.upload_workout.assert_called_once_with(payload)
        out = json.loads(capsys.readouterr().out)
        assert out[0]["workoutId"] == 99

    def test_create_from_stdin(self, mock_api, capsys, monkeypatch):
        payload = {"workoutName": "Stdin"}
        import io
        monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(payload)))
        mock_api.upload_workout.return_value = {"workoutId": 100}
        args = SimpleNamespace(command="create", files=["-"], pretty=False)
        rc = run(mock_api, args)
        assert rc == 0
        mock_api.upload_workout.assert_called_once_with(payload)


class TestWorkoutsDelete:
    def test_delete(self, mock_api, capsys):
        mock_api.delete_workout.return_value = None
        args = SimpleNamespace(command="delete", id=42, pretty=False)
        rc = run(mock_api, args)
        assert rc == 0
        mock_api.delete_workout.assert_called_once_with(42)
