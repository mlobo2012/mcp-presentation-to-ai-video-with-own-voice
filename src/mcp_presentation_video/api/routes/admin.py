"""Admin API routes for key management."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ..auth import (
    generate_api_key,
    list_api_keys,
    require_admin_key,
    revoke_api_key,
)
from ..models import APIKeyCreateRequest, APIKeyCreateResponse, APIKeyInfo

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


@router.post("/keys", response_model=APIKeyCreateResponse)
async def create_key(
    req: APIKeyCreateRequest,
    _: bool = Depends(require_admin_key),
) -> APIKeyCreateResponse:
    """Generate a new API key."""
    plaintext, record = generate_api_key(req.name)
    return APIKeyCreateResponse(
        key_id=record["key_id"],
        name=record["name"],
        api_key=plaintext,
    )


@router.get("/keys", response_model=list[APIKeyInfo])
async def get_keys(
    _: bool = Depends(require_admin_key),
) -> list[APIKeyInfo]:
    """List all API keys (without hashes)."""
    keys = list_api_keys()
    return [
        APIKeyInfo(key_id=k["key_id"], name=k["name"], created_at=k["created_at"])
        for k in keys
    ]


@router.delete("/keys/{key_id}")
async def delete_key(
    key_id: str,
    _: bool = Depends(require_admin_key),
) -> dict[str, str]:
    """Revoke an API key."""
    if not revoke_api_key(key_id):
        raise HTTPException(status_code=404, detail="Key not found")
    return {"message": f"Key {key_id} revoked"}
