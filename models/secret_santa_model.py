from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship, Session
from typing import TYPE_CHECKING, Any

from models.base import Base

if TYPE_CHECKING:
    from models.users_model import User

class SecretSantaContext(Base):
    __tablename__ = "secret_santa_contexts"
    id: Mapped[int] = mapped_column(primary_key=True)
    guild_id: Mapped[str] = mapped_column(unique=True)
    channel_id: Mapped[str] = mapped_column(unique=True, nullable=False)
    crazy_mode: Mapped[bool] = mapped_column(default=False, nullable=False)

    assignments: Mapped[list["SecretSantaAssignment"]] = relationship(
        "SecretSantaAssignment",
        back_populates="context",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"SecretSantaContext(id={self.id!r}, guild_id={self.guild_id!r}, channel_id={self.channel_id!r})"

class SecretSantaAssignment(Base):
    __tablename__ = "secret_santa_assignments"
    id: Mapped[int] = mapped_column(primary_key=True)
    context_id: Mapped[int] = mapped_column(ForeignKey("secret_santa_contexts.id"), nullable=False)
    gifter_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    receiver_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    # explicitly name target classes and which FK each relationship uses to resolve ambiguity
    context: Mapped["SecretSantaContext"] = relationship(
        "SecretSantaContext",
        back_populates="assignments",
    )
    gifter: Mapped["User"] = relationship(
        "User",
        foreign_keys=[gifter_id],
        back_populates="gifting_to",
    )
    receiver: Mapped["User"] = relationship(
        "User",
        foreign_keys=[receiver_id],
        back_populates="receiving_from",
    )

    def __init__(self, context: SecretSantaContext, gifter: "User", receiver: "User", **kw: Any):
        super().__init__(**kw)
        self.context = context
        self.gifter = gifter
        self.receiver = receiver

    def __repr__(self) -> str:
        return f"SecretSantaAssignment(id={self.id!r}, receiver_id={self.receiver_id!r}, gifter_id={self.gifter_id!r})"
