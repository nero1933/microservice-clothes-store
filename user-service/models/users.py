import uuid
from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy.dialects.postgresql import UUID

from db import Base


class User(Base):
	__tablename__ = 'users'

	id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
	email: Mapped[str] = mapped_column(unique=True, nullable=False)
	hashed_password: Mapped[str] = mapped_column(nullable=False)
	first_name: Mapped[str] = mapped_column(nullable=False)
	last_name: Mapped[str] = mapped_column(nullable=False)
	is_active: Mapped[bool] = mapped_column(default=False)
	is_admin: Mapped[bool] = mapped_column(default=False)
	created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

	def __repr__(self):
		return f"<User(email={self.email})>"
