"""API key authentication with bcrypt-hashed keys stored in JSON."""

from __future__ import annotations

import hashlib
import json
import secrets
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

import bcrypt
from fastapi import HTTPException, Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

_CONFIG_DIR = Path.home() / ".mcp-presentation-video"
_API_KEYS_FILE = _CONFIG_DIR / "api_keys.json"
_ADMIN_KEY_FILE = _CONFIG_DIR / "admin_key.txt"

_security = HTTPBearer()

# In-memory rate limiter: key_id -> list of request timestamps
_rate_limits: dict[str, list[float]] = defaultdict(list)
_RATE_LIMIT = 60  # requests per minute


def _load_keys() -> dict[str, Any]:
    if not _API_KEYS_FILE.exists():
        return {"keys": []}
    with open(_API_KEYS_FILE) as f:
        return json.load(f)


def _save_keys(data: dict[str, Any]) -> None:
    _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(_API_KEYS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def generate_api_key(name: str) -> tuple[str, dict[str, Any]]:
    """Generate a new API key. Returns (plaintext_key, key_record)."""
    raw = secrets.token_hex(32)
    plaintext = f"pv_live_{raw}"
    hashed = bcrypt.hashpw(plaintext.encode(), bcrypt.gensalt()).decode()
    key_id = hashlib.sha256(plaintext.encode()).hexdigest()[:16]

    from datetime import datetime, timezone

    record = {
        "key_id": key_id,
        "name": name,
        "hash": hashed,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    data = _load_keys()
    data["keys"].append(record)
    _save_keys(data)

    return plaintext, record


def list_api_keys() -> list[dict[str, str]]:
    """List all API keys (without hashes)."""
    data = _load_keys()
    return [
        {"key_id": k["key_id"], "name": k["name"], "created_at": k["created_at"]}
        for k in data["keys"]
    ]


def revoke_api_key(key_id: str) -> bool:
    """Revoke an API key by ID. Returns True if found and removed."""
    data = _load_keys()
    original_len = len(data["keys"])
    data["keys"] = [k for k in data["keys"] if k["key_id"] != key_id]
    if len(data["keys"]) < original_len:
        _save_keys(data)
        return True
    return False


def _verify_key(plaintext: str) -> dict[str, Any] | None:
    """Verify a plaintext API key against stored hashes. Returns key record or None."""
    data = _load_keys()
    for record in data["keys"]:
        if bcrypt.checkpw(plaintext.encode(), record["hash"].encode()):
            return record
    return None


def _check_rate_limit(key_id: str) -> None:
    """Raise 429 if rate limit exceeded."""
    now = time.time()
    window = [t for t in _rate_limits[key_id] if now - t < 60]
    _rate_limits[key_id] = window
    if len(window) >= _RATE_LIMIT:
        raise HTTPException(status_code=429, detail="Rate limit exceeded (60 req/min)")
    _rate_limits[key_id].append(now)


def get_admin_key() -> str:
    """Get or generate the admin key."""
    _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if _ADMIN_KEY_FILE.exists():
        return _ADMIN_KEY_FILE.read_text().strip()
    key = f"pv_admin_{secrets.token_hex(32)}"
    _ADMIN_KEY_FILE.write_text(key)
    _ADMIN_KEY_FILE.chmod(0o600)
    return key


def _verify_admin(plaintext: str) -> bool:
    """Check if the given key is the admin key."""
    admin_key = get_admin_key()
    return secrets.compare_digest(plaintext, admin_key)


async def require_api_key(
    credentials: HTTPAuthorizationCredentials = Security(_security),
) -> dict[str, Any]:
    """FastAPI dependency that validates the API key and enforces rate limiting."""
    token = credentials.credentials
    record = _verify_key(token)
    if record is None:
        raise HTTPException(status_code=401, detail="Invalid API key")
    _check_rate_limit(record["key_id"])
    return record


async def require_admin_key(
    credentials: HTTPAuthorizationCredentials = Security(_security),
) -> bool:
    """FastAPI dependency that validates the admin key."""
    token = credentials.credentials
    if not _verify_admin(token):
        raise HTTPException(status_code=403, detail="Admin key required")
    return True
