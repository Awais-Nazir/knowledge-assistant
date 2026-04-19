import uuid
from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy models.
    Every model inherits from this.
    """

    pass


class TimestampMixin:
    """
    Adds created_at and updated_at to any model that inherits it.
    These columns are managed automatically by the database — you
    never set them manually.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class UUIDMixin:
    """
    Adds a UUID primary key to any model that inherits it.
    We use UUIDs instead of integers for several reasons:
    - safe to expose in URLs (users can't guess other users' IDs)
    - unique across tables (useful for distributed systems)
    - can be generated in Python before hitting the database
    """

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )


# ```

# ---

## Why UUIDs instead of integers?

# This is a common beginner question. With integer IDs:
# ```
# GET /users/1
# GET /users/2
# GET /users/3    ← anyone can enumerate all users
# ```

# With UUID IDs:
# ```
# GET /users/3f7a9c2e-1b4d-4e8f-a2c1-9d0e3f5b7a1c
