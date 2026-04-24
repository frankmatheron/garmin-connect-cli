from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from garmin_connect_cli.commands.zones import (
    ZONES_PATH,
    _compute_floors,
    run,
)


CURRENT_ZONES = [
    {
        "trainingMethod": "HR_RESERVE",
        "restingHeartRateUsed": 55,
        "lactateThresholdHeartRateUsed": None,
        "zone1Floor": 117,
        "zone2Floor": 129,
        "zone3Floor": 142,
        "zone4Floor": 154,
        "zone5Floor": 167,
        "maxHeartRateUsed": 179,
        "restingHrAutoUpdateUsed": False,
        "sport": "DEFAULT",
        "changeState": "UNCHANGED",
    },
    {
        "trainingMethod": "HR_RESERVE",
        "restingHeartRateUsed": 55,
        "lactateThresholdHeartRateUsed": None,
        "zone1Floor": 117,
        "zone2Floor": 129,
        "zone3Floor": 142,
        "zone4Floor": 154,
        "zone5Floor": 167,
        "maxHeartRateUsed": 179,
        "restingHrAutoUpdateUsed": False,
        "sport": "RUNNING",
        "changeState": "UNCHANGED",
    },
]


class TestComputeFloors:
    def test_karvonen_190_47(self):
        # HRR = 143; floors at 50/60/70/80/90%
        assert _compute_floors("HR_RESERVE", 190, 47) == [118, 133, 147, 161, 176]

    def test_percent_max_190(self):
        # floors at 50/60/70/80/90% of max
        assert _compute_floors("PERCENT_MAX_HR", 190, 47) == [95, 114, 133, 152, 171]

    def test_unknown_method_raises(self):
        with pytest.raises(ValueError):
            _compute_floors("BOGUS", 190, 47)


class TestZonesList:
    def test_list_json(self, mock_api, capsys):
        mock_api.connectapi.return_value = CURRENT_ZONES
        args = SimpleNamespace(command="list", pretty=False)
        assert run(mock_api, args) == 0
        mock_api.connectapi.assert_called_once_with(ZONES_PATH)
        out = json.loads(capsys.readouterr().out)
        assert out[0]["sport"] == "DEFAULT"
        assert out[1]["sport"] == "RUNNING"

    def test_list_pretty(self, mock_api, capsys):
        mock_api.connectapi.return_value = CURRENT_ZONES
        args = SimpleNamespace(command="list", pretty=True)
        assert run(mock_api, args) == 0
        out = capsys.readouterr().out
        assert "DEFAULT" in out
        assert "RUNNING" in out
        assert "179" in out  # max HR shown


class TestZonesSet:
    def _args(self, **overrides):
        base = dict(
            command="set",
            max_hr=190,
            rhr=47,
            method="HR_RESERVE",
            sport="DEFAULT,RUNNING",
            zones=None,
            pretty=False,
        )
        base.update(overrides)
        return SimpleNamespace(**base)

    def test_set_applies_karvonen_floors_to_both_sports(self, mock_api, capsys):
        mock_api.connectapi.side_effect = [CURRENT_ZONES, CURRENT_ZONES]
        mock_api.client.request.return_value = MagicMock(status_code=204)

        assert run(mock_api, self._args()) == 0

        call = mock_api.client.request.call_args
        assert call.args[0] == "PUT"
        assert call.args[2] == ZONES_PATH
        sent = call.kwargs["json"]
        assert len(sent) == 2
        for entry in sent:
            assert entry["maxHeartRateUsed"] == 190
            assert entry["restingHeartRateUsed"] == 47
            assert entry["zone1Floor"] == 118
            assert entry["zone2Floor"] == 133
            assert entry["zone3Floor"] == 147
            assert entry["zone4Floor"] == 161
            assert entry["zone5Floor"] == 176
            assert entry["changeState"] == "CHANGED"

    def test_set_single_sport_leaves_other_untouched(self, mock_api):
        mock_api.connectapi.side_effect = [CURRENT_ZONES, CURRENT_ZONES]
        mock_api.client.request.return_value = MagicMock(status_code=204)

        assert run(mock_api, self._args(sport="RUNNING")) == 0

        sent = mock_api.client.request.call_args.kwargs["json"]
        by_sport = {e["sport"]: e for e in sent}
        assert by_sport["RUNNING"]["maxHeartRateUsed"] == 190
        assert by_sport["DEFAULT"]["maxHeartRateUsed"] == 179
        assert by_sport["DEFAULT"]["changeState"] == "UNCHANGED"

    def test_set_with_explicit_zones_override(self, mock_api):
        mock_api.connectapi.side_effect = [CURRENT_ZONES, CURRENT_ZONES]
        mock_api.client.request.return_value = MagicMock(status_code=204)

        assert run(mock_api, self._args(zones="120,135,150,165,180")) == 0

        sent = mock_api.client.request.call_args.kwargs["json"]
        assert sent[0]["zone1Floor"] == 120
        assert sent[0]["zone5Floor"] == 180

    def test_set_invalid_zones_returns_error(self, mock_api, capsys):
        mock_api.connectapi.return_value = CURRENT_ZONES

        assert run(mock_api, self._args(zones="120,135,150")) == 2
        err = capsys.readouterr().err
        assert "5 comma-separated" in err
        mock_api.client.request.assert_not_called()

    def test_set_unknown_sport_warns(self, mock_api, capsys):
        mock_api.connectapi.side_effect = [CURRENT_ZONES, CURRENT_ZONES]
        mock_api.client.request.return_value = MagicMock(status_code=204)

        assert run(mock_api, self._args(sport="CYCLING")) == 0
        err = capsys.readouterr().err
        assert "CYCLING" in err

    def test_set_put_failure_returns_error(self, mock_api, capsys):
        mock_api.connectapi.return_value = CURRENT_ZONES
        mock_api.client.request.return_value = MagicMock(
            status_code=400, text="bad request"
        )

        assert run(mock_api, self._args()) == 3
        err = capsys.readouterr().err
        assert "400" in err


class TestZonesUnknownCommand:
    def test_unknown_returns_error(self, mock_api, capsys):
        args = SimpleNamespace(command="frobnicate", pretty=False)
        assert run(mock_api, args) == 1
        err = capsys.readouterr().err
        assert "frobnicate" in err
