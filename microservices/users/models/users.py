import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, func, Enum
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy.dialects.postgresql import UUID

from core.db import Base


class RoleEnum(enum.Enum):
	user = "user"
	admin = "admin"
	moderator = "moderator"
	banned = "banned"


class User(Base):
	__tablename__ = 'users'

	id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
	email: Mapped[str] = mapped_column(unique=True, nullable=False, index=True)
	hashed_password: Mapped[str] = mapped_column(nullable=False)
	is_active: Mapped[bool] = mapped_column(default=False)
	role: Mapped[RoleEnum] = mapped_column(Enum(RoleEnum), default=RoleEnum.user, nullable=False)
	created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

	def __repr__(self):
		return f"<User(email={self.email})>"
