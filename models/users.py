from typing import List
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base import Base
from models.secret_santa import SecretSantaAssignment

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    discord_user_id: Mapped[str] = mapped_column(unique=True, nullable=False)
    gifting_to: Mapped[List["SecretSantaAssignment"]] = relationship(
        back_populates="gifter", cascade="all, delete-orphan"
    )
    receiving_from: Mapped[List["SecretSantaAssignment"]] = relationship(
        back_populates="receiver", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, discord_user_id={self.discord_user_id!r})"
