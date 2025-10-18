from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base import Base

class SecretSantaContext(Base):
    __tablename__ = "secret_santa_contexts"
    id: Mapped[int] = mapped_column(primary_key=True)
    guild_id: Mapped[str] = mapped_column(unique=True)
    channel_id: Mapped[str] = mapped_column(nullable=False)

    def __repr__(self) -> str:
        return f"SecretSantaContext(id={self.id!r}, guild_id={self.guild_id!r})"

class SecretSantaAssignment(Base):
    __tablename__ = "secret_santa_assignments"
    id: Mapped[int] = mapped_column(primary_key=True)
    context_id: Mapped[int] = mapped_column(ForeignKey("secret_santa_contexts.id"))
    context: Mapped["SecretSantaContext"] = relationship()
    gifter_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    gifter: Mapped["User"] = relationship(back_populates="gifting_to")
    receiver_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    receiver: Mapped["User"] = relationship(back_populates="receiving_from")

    def __init__(self, gifter, receiver, **kw: Any):
        super().__init__(**kw)
        self.gifter = gifter
        self.receiver = receiver

    def __repr__(self) -> str:
        return f"SecretSantaAssignment(id={self.id!r}, receiver_id={self.receiver_id!r}, gifter_id={self.gifter_id!r})"

    @classmethod
    def assign(cls, session, assignments: dict[str, set["User"]]) -> None:
        """Add and commit all SecretSantaAssignment objects from a dict of lists to the DB."""
        for gifter, receivers in assignments.items():
            for receiver in receivers:
                assignment = SecretSantaAssignment(gifter, receiver)
                session.add(assignment)
        session.commit()
