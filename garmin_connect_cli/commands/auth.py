from __future__ import annotations

import shutil
import sys
from getpass import getpass

from garmin_connect_cli.client import authenticate_and_persist, resolve_token_dir


def run_login(args) -> int:
    """Prompt for credentials, authenticate, and persist tokens."""
    username = input("Garmin username (email): ").strip()
    password = getpass("Garmin password: ")
    if not username or not password:
        print("ERROR: username and password are required", file=sys.stderr)
        raise SystemExit(2)

    authenticate_and_persist(username, password)
    print(f"Logged in as {username}")
    return 0


def run_logout(args) -> int:
    """Delete cached tokens. Idempotent."""
    token_dir = resolve_token_dir()
    if token_dir.exists():
        shutil.rmtree(token_dir)
    print("Logged out")
    return 0
