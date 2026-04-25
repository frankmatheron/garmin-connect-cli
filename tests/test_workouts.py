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
        args = SimpleNamespace(command="list", pretty=False, limit=None)
        rc = run(mock_api, args)
        assert rc == 0
        out = json.loads(capsys.readouterr().out)
        assert len(out) == 2
        assert out[0]["workoutId"] == 1

    def test_list_pages_through_full_library(self, mock_api, capsys):
        """When the library has > 100 workouts, list must page until empty."""
        full_page = [{"workoutId": i, "workoutName": f"W{i}"} for i in range(100)]
        partial_page = [{"workoutId": i, "workoutName": f"W{i}"} for i in range(100, 150)]
        mock_api.get_workouts.side_effect = [full_page, partial_page]

        args = SimpleNamespace(command="list", pretty=False, limit=None)
        rc = run(mock_api, args)
        assert rc == 0
        out = json.loads(capsys.readouterr().out)
        assert len(out) == 150
        # Verify offset progression
        assert mock_api.get_workouts.call_args_list[0].kwargs == {"start": 0, "limit": 100}
        assert mock_api.get_workouts.call_args_list[1].kwargs == {"start": 100, "limit": 100}

    def test_list_stops_on_empty_page(self, mock_api, capsys):
        """Empty page short-circuits — no extra request."""
        full_page = [{"workoutId": i, "workoutName": f"W{i}"} for i in range(100)]
        mock_api.get_workouts.side_effect = [full_page, []]

        args = SimpleNamespace(command="list", pretty=False, limit=None)
        rc = run(mock_api, args)
        assert rc == 0
        out = json.loads(capsys.readouterr().out)
        assert len(out) == 100
        assert mock_api.get_workouts.call_count == 2

    def test_list_with_limit_caps_results(self, mock_api, capsys):
        """--limit caps total returned and stops paging early."""
        full_page = [{"workoutId": i, "workoutName": f"W{i}"} for i in range(100)]
        mock_api.get_workouts.return_value = full_page

        args = SimpleNamespace(command="list", pretty=False, limit=5)
        rc = run(mock_api, args)
        assert rc == 0
        out = json.loads(capsys.readouterr().out)
        assert len(out) == 5
        # Only one request, page_size narrowed to limit
        mock_api.get_workouts.assert_called_once_with(start=0, limit=5)


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


class TestWorkoutsUpdate:
    def test_update_from_file(self, mock_api, capsys, tmp_path):
        payload = {"workoutId": 42, "workoutName": "Updated", "description": "new"}
        f = tmp_path / "w.json"
        f.write_text(json.dumps(payload))
        # PUT returns success
        mock_api.client.request.return_value = SimpleNamespace(status_code=200, text="")
        # Subsequent fetch returns updated state
        mock_api.get_workout_by_id.return_value = payload

        args = SimpleNamespace(command="update", id=42, file=str(f), pretty=False)
        rc = run(mock_api, args)
        assert rc == 0
        mock_api.client.request.assert_called_once_with(
            "PUT", "connectapi", "/workout-service/workout/42", json=payload
        )
        out = json.loads(capsys.readouterr().out)
        assert out["workoutId"] == 42
        assert out["description"] == "new"

    def test_update_from_stdin(self, mock_api, capsys, monkeypatch):
        payload = {"workoutId": 42, "workoutName": "From stdin"}
        import io
        monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(payload)))
        mock_api.client.request.return_value = SimpleNamespace(status_code=200, text="")
        mock_api.get_workout_by_id.return_value = payload

        args = SimpleNamespace(command="update", id=42, file="-", pretty=False)
        rc = run(mock_api, args)
        assert rc == 0
        mock_api.client.request.assert_called_once_with(
            "PUT", "connectapi", "/workout-service/workout/42", json=payload
        )

    def test_update_returns_3_on_api_error(self, mock_api, capsys, tmp_path):
        f = tmp_path / "w.json"
        f.write_text(json.dumps({"workoutId": 42}))
        mock_api.client.request.return_value = SimpleNamespace(status_code=400, text="bad")

        args = SimpleNamespace(command="update", id=42, file=str(f), pretty=False)
        rc = run(mock_api, args)
        assert rc == 3
        # No fetch attempted on error
        mock_api.get_workout_by_id.assert_not_called()

    def test_update_falls_back_when_fetch_fails(self, mock_api, capsys, tmp_path):
        """If the post-update fetch raises, still return success with a stub."""
        f = tmp_path / "w.json"
        f.write_text(json.dumps({"workoutId": 42, "workoutName": "x"}))
        mock_api.client.request.return_value = SimpleNamespace(status_code=200, text="")
        mock_api.get_workout_by_id.side_effect = RuntimeError("transient")

        args = SimpleNamespace(command="update", id=42, file=str(f), pretty=False)
        rc = run(mock_api, args)
        assert rc == 0
        out = json.loads(capsys.readouterr().out)
        assert out == {"updated": 42}
