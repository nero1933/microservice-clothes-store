import uuid
import datetime

from sqlalchemy import String, DateTime, Boolean
from sqlalchemy.orm import mapped_column
from sqlalchemy.dialects.postgresql import UUID

from db import Base


class User(Base):
    __tablename__ = 'users'

    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = mapped_column(String, unique=True, nullable=False)
    hashed_password = mapped_column(String, nullable=False)
    first_name = mapped_column(String, nullable=False)
    last_name = mapped_column(String, nullable=False)
    is_active = mapped_column(Boolean, default=False)
    is_admin = mapped_column(Boolean, default=False)
    created_at = mapped_column(DateTime, default=datetime.timezone.utc)

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, role={self.is_admin})>"