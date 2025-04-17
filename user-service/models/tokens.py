import uuid

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from db import Base


class TokenBlacklist(Base):
	__tablename__ = "token_blacklist"

	jti: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, index=True)  # JWT ID

	def __repr__(self):
		return f"<TokenBlacklist jti={self.jti}>"
