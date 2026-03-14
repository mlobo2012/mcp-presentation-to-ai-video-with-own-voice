"""Pydantic models for API request/response schemas."""

from __future__ import annotations

from pydantic import BaseModel


class JobCreateResponse(BaseModel):
    job_id: str
    status: str = "pending"


class JobStatus(BaseModel):
    job_id: str
    status: str
    progress: str = ""
    video_url: str | None = None
    error: str | None = None
    created_at: str = ""
    updated_at: str = ""


class JobListItem(BaseModel):
    job_id: str
    status: str
    created_at: str
    updated_at: str


class VoiceInfo(BaseModel):
    name: str
    description: str = ""
    registered_at: str = ""


class VoiceCreateResponse(BaseModel):
    name: str
    message: str


class APIKeyCreateRequest(BaseModel):
    name: str


class APIKeyInfo(BaseModel):
    key_id: str
    name: str
    created_at: str


class APIKeyCreateResponse(BaseModel):
    key_id: str
    name: str
    api_key: str
    message: str = "Save this key — it will not be shown again."


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "0.1.0"
