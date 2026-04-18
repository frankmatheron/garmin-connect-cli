from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest


class TestLogoutCommand:
    def test_logout_when_tokens_exist(self, monkeypatch, tmp_path, capsys):
        """logout should delete the token directory contents."""
        from garmin_connect_cli.commands.auth import run_logout

        token_dir = tmp_path / "garmin-connect-cli" / "tokens"
        token_dir.mkdir(parents=True)
        (token_dir / "oauth1_token").write_text("fake-token")
        (token_dir / "oauth2_token").write_text("fake-token")

        monkeypatch.setenv("GARMIN_TOKEN_DIR", str(tmp_path))

        rc = run_logout(SimpleNamespace())
        assert rc == 0
        assert not (token_dir / "oauth1_token").exists()
        assert not (token_dir / "oauth2_token").exists()
        assert not token_dir.exists()
        assert token_dir.parent.exists()  # garmin-connect-cli/ parent left as-is
        assert "Logged out" in capsys.readouterr().out

    def test_logout_when_no_tokens_is_idempotent(self, monkeypatch, tmp_path, capsys):
        """logout should succeed when no tokens exist."""
        from garmin_connect_cli.commands.auth import run_logout

        monkeypatch.setenv("GARMIN_TOKEN_DIR", str(tmp_path))

        rc = run_logout(SimpleNamespace())
        assert rc == 0
        assert "Logged out" in capsys.readouterr().out


class TestLoginCommand:
    def test_login_prompts_and_writes_tokens(self, monkeypatch, tmp_path, capsys):
        """login should prompt for credentials and call Garmin.login()."""
        from garmin_connect_cli.commands import auth

        monkeypatch.setenv("GARMIN_TOKEN_DIR", str(tmp_path))
        monkeypatch.setattr("builtins.input", lambda prompt="": "me@example.com")
        monkeypatch.setattr(auth, "getpass", lambda prompt="": "hunter2")

        fake_api = MagicMock()
        fake_api.client = MagicMock()
        with patch("garmin_connect_cli.client.Garmin", return_value=fake_api) as mock_cls:
            rc = auth.run_login(SimpleNamespace())

        assert rc == 0
        mock_cls.assert_called_once_with("me@example.com", "hunter2")
        expected_token_dir = tmp_path / "garmin-connect-cli" / "tokens"
        fake_api.login.assert_called_once_with(tokenstore=str(expected_token_dir))
        fake_api.client.dump.assert_called_once_with(str(expected_token_dir))
        assert "Logged in as me@example.com" in capsys.readouterr().out

    def test_login_authentication_error_exits_2(self, monkeypatch, tmp_path, capsys):
        """login should exit 2 on auth failure."""
        from garminconnect import GarminConnectAuthenticationError

        from garmin_connect_cli.commands import auth

        monkeypatch.setenv("GARMIN_TOKEN_DIR", str(tmp_path))
        monkeypatch.setattr("builtins.input", lambda prompt="": "me@example.com")
        monkeypatch.setattr(auth, "getpass", lambda prompt="": "wrong")

        fake_api = MagicMock()
        fake_api.login.side_effect = GarminConnectAuthenticationError("bad creds")
        with patch("garmin_connect_cli.client.Garmin", return_value=fake_api):
            with pytest.raises(SystemExit) as excinfo:
                auth.run_login(SimpleNamespace())

        assert excinfo.value.code == 2
        assert "authentication failed" in capsys.readouterr().err

    def test_login_empty_username_exits_2(self, monkeypatch, tmp_path, capsys):
        """login should refuse empty input."""
        from garmin_connect_cli.commands import auth

        monkeypatch.setenv("GARMIN_TOKEN_DIR", str(tmp_path))
        monkeypatch.setattr("builtins.input", lambda prompt="": "")
        monkeypatch.setattr(auth, "getpass", lambda prompt="": "some-password")

        with pytest.raises(SystemExit) as excinfo:
            auth.run_login(SimpleNamespace())

        assert excinfo.value.code == 2
        assert "username and password are required" in capsys.readouterr().err

    def test_login_rate_limit_error_exits_3(self, monkeypatch, tmp_path, capsys):
        """login should exit 3 on rate limit error."""
        from garminconnect import GarminConnectTooManyRequestsError

        from garmin_connect_cli.commands import auth

        monkeypatch.setenv("GARMIN_TOKEN_DIR", str(tmp_path))
        monkeypatch.setattr("builtins.input", lambda prompt="": "me@example.com")
        monkeypatch.setattr(auth, "getpass", lambda prompt="": "pw")

        fake_api = MagicMock()
        fake_api.login.side_effect = GarminConnectTooManyRequestsError("rate limited")
        with patch("garmin_connect_cli.client.Garmin", return_value=fake_api):
            with pytest.raises(SystemExit) as excinfo:
                auth.run_login(SimpleNamespace())

        assert excinfo.value.code == 3
        assert "rate limited" in capsys.readouterr().err
