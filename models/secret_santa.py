from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base import Base

class SecretSantaAssignment(Base):
    __tablename__ = "secret_santa_assignments"
    id: Mapped[int] = mapped_column(primary_key=True)
    receiver_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    receiver: Mapped["User"] = relationship(back_populates="receiving_from")
    gifter_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    gifter: Mapped["User"] = relationship(back_populates="gifting_to")

    def __repr__(self) -> str:
        return f"SecretSantaAssignment(id={self.id!r}, receiver_id={self.receiver_id!r}, gifter_id={self.gifter_id!r})"
