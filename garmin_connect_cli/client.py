from __future__ import annotations

import os
import sys
from pathlib import Path

from garminconnect import (
    Garmin,
    GarminConnectAuthenticationError,
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
)


def _load_env(env_path: Path) -> dict[str, str]:
    if not env_path.exists():
        return {}
    out: dict[str, str] = {}
    for raw in env_path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        out[key.strip()] = val.strip().strip('"').strip("'")
    return out


def resolve_credentials(
    env_path: Path | None = None,
) -> tuple[str, str]:
    """Resolve Garmin credentials: env vars first, then .env file."""
    username = os.environ.get("GARMIN_USERNAME")
    password = os.environ.get("GARMIN_PASSWORD")
    if username and password:
        return username, password

    if env_path is None:
        env_path = Path.cwd() / ".env"
    env = _load_env(env_path)
    username = username or env.get("GARMIN_USERNAME")
    password = password or env.get("GARMIN_PASSWORD")

    if not username or not password:
        print(
            "ERROR: Not logged in. Run 'garmin login', or set GARMIN_USERNAME / "
            "GARMIN_PASSWORD environment variables or a .env file for automation.",
            file=sys.stderr,
        )
        raise SystemExit(2)
    return username, password


def resolve_token_dir() -> Path:
    """Resolve the token cache directory using XDG conventions.

    Priority: GARMIN_TOKEN_DIR > XDG_DATA_HOME > ~/.local/share, each
    suffixed with 'garmin-connect-cli/tokens'.
    """
    override = os.environ.get("GARMIN_TOKEN_DIR")
    if override:
        base = Path(override)
    else:
        xdg = os.environ.get("XDG_DATA_HOME")
        base = Path(xdg) if xdg else Path.home() / ".local" / "share"
    return base / "garmin-connect-cli" / "tokens"


def authenticate_and_persist(username: str, password: str) -> Garmin:
    """Authenticate with Garmin and persist session tokens.

    Resolves the token directory, logs in, and dumps tokens. Raises
    SystemExit(2) on authentication failure and SystemExit(3) on
    connection or rate-limit errors.
    """
    token_dir = resolve_token_dir()
    token_dir.mkdir(parents=True, exist_ok=True)
    tokenstore = str(token_dir)
    try:
        api = Garmin(username, password)
        api.login(tokenstore=tokenstore)
    except GarminConnectAuthenticationError as e:
        print(f"ERROR: authentication failed: {e}", file=sys.stderr)
        raise SystemExit(2)
    except (GarminConnectConnectionError, GarminConnectTooManyRequestsError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        raise SystemExit(3)
    api.client.dump(tokenstore)
    return api


def login(env_path: Path | None = None) -> Garmin:
    """Authenticate via cached tokens if available, otherwise via credentials.

    Priority: cached tokens at the configured token directory → env vars /
    .env credentials → error pointing at `garmin login`. Rate-limit and
    connection errors during the cached-token path propagate as SystemExit(3);
    authentication errors on the cached path fall through to the credential
    flow (the cache is probably stale).
    """
    token_dir = resolve_token_dir()
    if token_dir.exists() and any(token_dir.iterdir()):
        try:
            api = Garmin()
            api.login(tokenstore=str(token_dir))
            return api
        except GarminConnectAuthenticationError:
            pass
        except (GarminConnectConnectionError, GarminConnectTooManyRequestsError) as e:
            print(f"ERROR: {e}", file=sys.stderr)
            raise SystemExit(3)

    username, password = resolve_credentials(env_path)
    return authenticate_and_persist(username, password)
