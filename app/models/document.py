import uuid
from sqlalchemy import String, Integer, Text, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.models.base import Base, TimestampMixin, UUIDMixin


class DocumentStatus(str, enum.Enum):
    """
    Represents every possible state a document can be in.
    Using an Enum instead of plain strings prevents typos —
    you can't accidentally write "proccessing" or "READY".
    """
    PENDING    = "PENDING"      # just uploaded, job not started
    PROCESSING = "PROCESSING"   # background job is running
    READY      = "READY"        # chunks + embeddings stored, ready to chat
    FAILED     = "FAILED"       # something went wrong during processing


class Document(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "documents"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    original_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    mime_type: Mapped[str] = mapped_column(
        String(127),
        nullable=False,
    )
    file_size: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    storage_path: Mapped[str] = mapped_column(
        String(1024),
        nullable=False,
    )
    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus, name="document_status", create_type=True),
        nullable=False,
        default=DocumentStatus.PENDING,
        server_default=DocumentStatus.PENDING.value,
        index=True,
    )
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    chunk_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    # ── Relationships ──────────────────────────────────────
    user: Mapped["User"] = relationship(
        back_populates="documents",
    )
    chunks: Mapped[list["DocumentChunk"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
    )