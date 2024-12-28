"""Defines the model for validating and managing extension configuration."""

# Standard Python Libraries
import logging
from typing import Any, Dict

# Third-Party Libraries
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from . import MQTTConfig, StationInfo
from .. import UnitSystem

logger = logging.getLogger(__name__)


class ExtensionConfig(BaseModel):
    """Configuration model for the extension configuration."""

    model_config = ConfigDict(extra="forbid")

    discovery_topic_prefix: str = Field(
        default="homeassistant", description="Prefix for the MQTT discovery topic"
    )
    mqtt: MQTTConfig = Field(..., description="MQTT broker configuration")
    node_id: str = Field(
        ...,
        description="Unique identifier for the Home Assistant node",
        min_length=1,
        pattern=r"^[a-zA-Z0-9_-]+$",
    )
    state_topic_prefix: str = Field(
        default="weather", description="Prefix for the state topic"
    )
    station: StationInfo = Field(..., description="Weather station device information")
    unit_system: UnitSystem = Field(
        default=UnitSystem.METRICWX, description="Unit system for measurements"
    )

    @classmethod
    def from_config_dict(
        cls, config_dict: Dict[str, Any], key: str
    ) -> "ExtensionConfig":
        """Create an instance from a configuration dictionary."""
        extension_config = config_dict.get(key, {})
        try:
            return cls(**extension_config)
        except ValidationError as e:
            logger.error(f"Configuration validation error: {e}")
            raise e
