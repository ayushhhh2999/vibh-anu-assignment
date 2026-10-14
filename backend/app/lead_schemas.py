
from datetime import date, datetime, time

from pydantic import BaseModel, ConfigDict, Field


class LeadCreate(BaseModel):
    """Fields Marketing is allowed to submit."""

    name: str = Field(min_length=2, max_length=100)
    contact_number: str = Field(min_length=7, max_length=20)


class LeadListResponse(BaseModel):
    """Fields returned when displaying a lead."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    contact_number: str | None = None
    postal_address: str | None = None
    meeting_date: date | None = None
    meeting_time: time | None = None
    remark: str | None = None
    audio_available: bool
    status: str
    created_at: datetime
