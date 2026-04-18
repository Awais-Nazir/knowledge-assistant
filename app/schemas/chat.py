import uuid
from datetime import datetime
from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    session_id: uuid.UUID | None = None


class CitationResponse(BaseModel):
    chunk_id: str
    document_name: str
    page_number: int | None = None
    content_preview: str


class MessageResponse(BaseModel):
    id: uuid.UUID
    role: str
    content: str
    citations: list[CitationResponse] | None = None
    created_at: float

    model_config = {"from_attributes": True}


class SessionResponse(BaseModel):
    id: uuid.UUID
    title: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SessionListResponse(BaseModel):
    items: list[SessionResponse]
    total: int
    page: int
    page_size: int
    has_next: bool
    has_previous: bool


class SessionDetailResponse(BaseModel):
    session: SessionResponse
    messages: list[MessageResponse]