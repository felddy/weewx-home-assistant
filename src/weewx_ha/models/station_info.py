"""Defines the model for describing a weather station device."""

# Standard Python Libraries
import logging

# Third-Party Libraries
from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)


class StationInfo(BaseModel):
    """Model for describing a weather station device."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(
        ...,
        description="Name of the weather station.",
        min_length=1,
    )
    model: str = Field(
        ...,
        description="Model of the weather station.",
        min_length=1,
    )
    manufacturer: str = Field(
        ...,
        description="Manufacturer of the weather station.",
        min_length=1,
    )
