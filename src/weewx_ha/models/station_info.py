"""Defines the model for describing a weather station device."""

# Standard Python Libraries
import logging
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

# Third-Party Libraries
from pydantic import BaseModel, ConfigDict, Field, field_validator

logger = logging.getLogger(__name__)


class StationInfo(BaseModel):
    """Model for describing a weather station device."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., description="Name of the weather station.", min_length=1)
    model: str = Field(..., description="Model of the weather station.", min_length=1)
    manufacturer: str = Field(
        ..., description="Manufacturer of the weather station.", min_length=1
    )
    time_zone: ZoneInfo = Field(
        default_factory=lambda: ZoneInfo("UTC"),
        description="Time zone of the weather station.",
    )

    @field_validator("time_zone", mode="before")
    def validate_time_zone(cls, value):
        """Validate the time_zone field to ensure it's a valid ZoneInfo object."""
        if isinstance(value, ZoneInfo):
            return value
        try:
            return ZoneInfo(value)
        except ZoneInfoNotFoundError:
            raise ValueError(f"Invalid time zone: {value}")
