
from datetime import date, time, datetime

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    Time,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import UniqueConstraint
from app.db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True
    )
    full_name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True
    )
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(30))

    created_leads: Mapped[list["Lead"]] = relationship(
        back_populates="creator",
        foreign_keys="Lead.created_by_id",
    )

    claimed_leads: Mapped[list["Lead"]] = relationship(
        back_populates="claimer",
        foreign_keys="Lead.claimed_by_id",
    )


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True
    )
    name: Mapped[str] = mapped_column(String(100))
    contact_number: Mapped[str] = mapped_column(String(20))

    postal_address: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    meeting_date: Mapped[date | None] = mapped_column(
        Date, nullable=True
    )
    meeting_time: Mapped[time | None] = mapped_column(
        Time, nullable=True
    )
    remark: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )

    audio_path: Mapped[str | None] = mapped_column(
        String(500), nullable=True
    )

    status: Mapped[str] = mapped_column(
        String(30), default="communication"
    )

    created_by_id: Mapped[int] = mapped_column(
        ForeignKey("users.id")
    )
    claimed_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )

    creator: Mapped["User"] = relationship(
        back_populates="created_leads",
        foreign_keys=[created_by_id],
    )

    claimer: Mapped["User | None"] = relationship(
        back_populates="claimed_leads",
        foreign_keys=[claimed_by_id],
    )


class AudioPlayback(Base):
    __tablename__ = "audio_playbacks"

    __table_args__ = (
        UniqueConstraint(
            "lead_id",
            "user_id",
            name="uq_audio_playback_lead_user",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    lead_id: Mapped[int] = mapped_column(
        ForeignKey("leads.id"),
        index=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        index=True,
    )

    completed_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )
