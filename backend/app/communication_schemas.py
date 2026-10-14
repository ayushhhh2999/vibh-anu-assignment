
from datetime import date, time

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CommunicationUpdate(BaseModel):
    """Fields Communication is allowed to edit."""

    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=2, max_length=100)
    postal_address: str | None = Field(default=None, min_length=5)
    meeting_date: date | None = None
    meeting_time: time | None = None
    remark: str | None = None

    @model_validator(mode="after")
    def check_at_least_one_field(self):
        if not self.model_fields_set:
            raise ValueError("Provide at least one field to update.")
        return self
