from models.base import Base

from typing import List, TYPE_CHECKING
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from models.secret_santa_model import SecretSantaAssignment

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    discord_user_id: Mapped[str] = mapped_column(unique=True, nullable=False)
    nomnoms: Mapped[int] = mapped_column(default=0, nullable=False)

    gifting_to: Mapped[List["SecretSantaAssignment"]] = relationship(
        "SecretSantaAssignment",
        back_populates="gifter",
        cascade="all, delete-orphan",
        foreign_keys='SecretSantaAssignment.gifter_id',
        order_by='SecretSantaAssignment.id',
    )
    receiving_from: Mapped[List["SecretSantaAssignment"]] = relationship(
        "SecretSantaAssignment",
        back_populates="receiver",
        cascade="all, delete-orphan",
        foreign_keys='SecretSantaAssignment.receiver_id',
        order_by='SecretSantaAssignment.id',
    )

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, discord_user_id={self.discord_user_id!r})"

    @classmethod
    def get_or_create(cls, session, discord_user_id: str) -> "User":
        """Get a user by discord_user_id, or create if not exists."""
        user = session.query(cls).filter_by(discord_user_id=discord_user_id).first()
        if user:
            return user

        user = cls(discord_user_id=discord_user_id)
        session.add(user)
        session.commit()
        return user
