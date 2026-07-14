from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class PersonRelation(Base):
    __tablename__ = "person_relations"
    __table_args__ = (
        UniqueConstraint(
            "family_id",
            "from_person_id",
            "to_person_id",
            "relation_type",
            name="uk_relation",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    family_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("families.id"), nullable=False, index=True
    )
    from_person_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("persons.id"), nullable=False, index=True
    )
    to_person_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("persons.id"), nullable=False, index=True
    )
    relation_type: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    from_person = relationship("Person", foreign_keys=[from_person_id])
    to_person = relationship("Person", foreign_keys=[to_person_id])
