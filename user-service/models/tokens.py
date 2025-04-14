import uuid

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from .users import Base


class BlacklistedToken(Base):
    __tablename__ = "blacklisted_tokens"

    jti: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, index=True)  # JWT ID

    def __repr__(self):
        return f"<BlacklistedToken jti={self.jti}>"
