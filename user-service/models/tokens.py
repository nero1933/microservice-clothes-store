import uuid
from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from db import Base


class BlacklistedToken(Base):
    __tablename__ = "blacklisted_tokens"

    jti: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, index=True)  # JWT ID

    def __repr__(self):
        return f"<BlacklistedToken jti={self.jti}>"
