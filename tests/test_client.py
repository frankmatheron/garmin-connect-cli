from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from garmin_connect_cli.client import login, resolve_credentials, resolve_token_dir


class TestResolveCredentials:
    def test_env_vars_take_precedence(self, monkeypatch, tmp_path):
        """Env vars should win over .env file."""
        env_file = tmp_path / ".env"
        env_file.write_text("GARMIN_USERNAME=file_user\nGARMIN_PASSWORD=file_pass\n")
        monkeypatch.setenv("GARMIN_USERNAME", "env_user")
        monkeypatch.setenv("GARMIN_PASSWORD", "env_pass")
        user, pw = resolve_credentials(env_path=env_file)
        assert user == "env_user"
        assert pw == "env_pass"

    def test_falls_back_to_env_file(self, monkeypatch, tmp_path):
        """When no env vars, read from .env file."""
        monkeypatch.delenv("GARMIN_USERNAME", raising=False)
        monkeypatch.delenv("GARMIN_PASSWORD", raising=False)
        env_file = tmp_path / ".env"
        env_file.write_text('GARMIN_USERNAME=file_user\nGARMIN_PASSWORD="file_pass"\n')
        user, pw = resolve_credentials(env_path=env_file)
        assert user == "file_user"
        assert pw == "file_pass"

    def test_missing_credentials_raises(self, monkeypatch, tmp_path):
        """Should raise SystemExit when credentials can't be found."""
        monkeypatch.delenv("GARMIN_USERNAME", raising=False)
        monkeypatch.delenv("GARMIN_PASSWORD", raising=False)
        env_file = tmp_path / ".env"
        env_file.write_text("# empty\n")
        with pytest.raises(SystemExit):
            resolve_credentials(env_path=env_file)

    def test_missing_env_file_no_env_vars_raises(self, monkeypatch, tmp_path):
        """Should raise SystemExit when .env doesn't exist and no env vars."""
        monkeypatch.delenv("GARMIN_USERNAME", raising=False)
        monkeypatch.delenv("GARMIN_PASSWORD", raising=False)
        env_file = tmp_path / ".env_nonexistent"
        with pytest.raises(SystemExit):
            resolve_credentials(env_path=env_file)


class TestResolveTokenDir:
    def test_explicit_garmin_token_dir_env_var(self, monkeypatch, tmp_path):
        """GARMIN_TOKEN_DIR takes highest priority."""
        override = tmp_path / "custom"
        monkeypatch.setenv("GARMIN_TOKEN_DIR", str(override))
        monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "xdg"))
        monkeypatch.setenv("HOME", str(tmp_path / "home"))

        result = resolve_token_dir()
        assert result == override / "garmin-connect-cli" / "tokens"

    def test_xdg_data_home_when_no_override(self, monkeypatch, tmp_path):
        """XDG_DATA_HOME is used when GARMIN_TOKEN_DIR unset."""
        monkeypatch.delenv("GARMIN_TOKEN_DIR", raising=False)
        xdg = tmp_path / "xdg"
        monkeypatch.setenv("XDG_DATA_HOME", str(xdg))

        result = resolve_token_dir()
        assert result == xdg / "garmin-connect-cli" / "tokens"

    def test_home_default_when_nothing_set(self, monkeypatch, tmp_path):
        """Falls back to ~/.local/share when no env vars."""
        monkeypatch.delenv("GARMIN_TOKEN_DIR", raising=False)
        monkeypatch.delenv("XDG_DATA_HOME", raising=False)
        monkeypatch.setenv("HOME", str(tmp_path))

        result = resolve_token_dir()
        assert result == tmp_path / ".local" / "share" / "garmin-connect-cli" / "tokens"

    def test_empty_garmin_token_dir_falls_through(self, monkeypatch, tmp_path):
        """Empty GARMIN_TOKEN_DIR should be treated as unset."""
        monkeypatch.setenv("GARMIN_TOKEN_DIR", "")
        xdg = tmp_path / "xdg"
        monkeypatch.setenv("XDG_DATA_HOME", str(xdg))

        result = resolve_token_dir()
        assert result == xdg / "garmin-connect-cli" / "tokens"

    def test_empty_xdg_data_home_falls_through(self, monkeypatch, tmp_path):
        """Empty XDG_DATA_HOME should be treated as unset."""
        monkeypatch.delenv("GARMIN_TOKEN_DIR", raising=False)
        monkeypatch.setenv("XDG_DATA_HOME", "")
        monkeypatch.setenv("HOME", str(tmp_path))

        result = resolve_token_dir()
        assert result == tmp_path / ".local" / "share" / "garmin-connect-cli" / "tokens"


class TestLogin:
    def test_cached_tokens_short_circuit_credential_lookup(self, monkeypatch, tmp_path):
        """When valid tokens exist, login() must not consult env vars or .env."""
        token_dir = tmp_path / "garmin-connect-cli" / "tokens"
        token_dir.mkdir(parents=True)
        (token_dir / "garmin_tokens.json").write_text("{}")

        monkeypatch.setenv("GARMIN_TOKEN_DIR", str(tmp_path))
        monkeypatch.delenv("GARMIN_USERNAME", raising=False)
        monkeypatch.delenv("GARMIN_PASSWORD", raising=False)

        fake_api = MagicMock()
        with patch("garmin_connect_cli.client.Garmin", return_value=fake_api) as mock_cls:
            result = login(env_path=tmp_path / ".env_nonexistent")

        assert result is fake_api
        mock_cls.assert_called_once_with()  # no email/password args
        fake_api.login.assert_called_once_with(tokenstore=str(token_dir))

    def test_empty_token_dir_falls_back_to_credentials(self, monkeypatch, tmp_path):
        """An empty token dir should trigger the credential path."""
        token_dir = tmp_path / "garmin-connect-cli" / "tokens"
        token_dir.mkdir(parents=True)  # exists but empty

        monkeypatch.setenv("GARMIN_TOKEN_DIR", str(tmp_path))
        monkeypatch.setenv("GARMIN_USERNAME", "u")
        monkeypatch.setenv("GARMIN_PASSWORD", "p")

        fake_api = MagicMock()
        with patch("garmin_connect_cli.client.Garmin", return_value=fake_api) as mock_cls:
            login()

        # Credential path constructs with username/password
        mock_cls.assert_called_once_with("u", "p")

    def test_invalid_cached_tokens_fall_back_to_credentials(self, monkeypatch, tmp_path):
        """Auth errors when loading tokens should fall through to the credential flow."""
        from garminconnect import GarminConnectAuthenticationError

        token_dir = tmp_path / "garmin-connect-cli" / "tokens"
        token_dir.mkdir(parents=True)
        (token_dir / "garmin_tokens.json").write_text("{}")

        monkeypatch.setenv("GARMIN_TOKEN_DIR", str(tmp_path))
        monkeypatch.setenv("GARMIN_USERNAME", "u")
        monkeypatch.setenv("GARMIN_PASSWORD", "p")

        # First Garmin() call (token-only) raises; second (credential) succeeds.
        stale_api = MagicMock()
        stale_api.login.side_effect = GarminConnectAuthenticationError("stale")
        fresh_api = MagicMock()

        with patch(
            "garmin_connect_cli.client.Garmin", side_effect=[stale_api, fresh_api]
        ) as mock_cls:
            result = login()

        assert result is fresh_api
        assert mock_cls.call_count == 2
        # First call: no args (token-only). Second: with credentials.
        assert mock_cls.call_args_list[0].args == ()
        assert mock_cls.call_args_list[1].args == ("u", "p")

    def test_rate_limit_during_cached_login_propagates(self, monkeypatch, tmp_path):
        """Rate limit errors during cached-token login must propagate, not silently re-prompt."""
        from garminconnect import GarminConnectTooManyRequestsError

        token_dir = tmp_path / "garmin-connect-cli" / "tokens"
        token_dir.mkdir(parents=True)
        (token_dir / "garmin_tokens.json").write_text("{}")

        monkeypatch.setenv("GARMIN_TOKEN_DIR", str(tmp_path))

        fake_api = MagicMock()
        fake_api.login.side_effect = GarminConnectTooManyRequestsError("rate limited")

        with patch("garmin_connect_cli.client.Garmin", return_value=fake_api):
            with pytest.raises(SystemExit) as excinfo:
                login()

        assert excinfo.value.code == 3
