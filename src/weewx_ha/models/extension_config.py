"""Defines the model for validating and managing extension configuration."""

# Standard Python Libraries
import logging
from typing import Any, Dict

# Third-Party Libraries
from pydantic import (
    AnyUrl,
    BaseModel,
    ConfigDict,
    Field,
    Secret,
    ValidationError,
    field_validator,
)

from .. import UnitSystem

logger = logging.getLogger(__name__)


class ExtensionConfig(BaseModel):
    """Configuration model for the extension configuration."""

    model_config = ConfigDict(extra="forbid")

    discovery_topic_prefix: str = Field(
        default="homeassistant", description="Prefix for the discovery topic"
    )
    filter_keys: set[str] = Field(
        default_factory=lambda: {"dateTime"}, description="Keys to filter data"
    )
    node_id: str = Field(
        ...,
        description="Unique identifier for the Home Assistant node",
        min_length=1,
        pattern=r"^[a-zA-Z0-9_-]+$",
    )
    server_url: Secret[AnyUrl] = Field(..., description="URL of the MQTT server")
    state_topic_prefix: str = Field(
        default="weather", description="Prefix for the state topic"
    )
    unit_system: UnitSystem = Field(
        default=UnitSystem.METRICWX, description="Unit system for measurements"
    )

    # Custom validator to convert comma-delimited string to set for filter_keys
    @classmethod
    @field_validator("filter_keys", mode="before")
    def validate_filter_keys(cls, value: Any) -> set[str]:
        """Validate and convert the input value to a set of filter keys."""
        if isinstance(value, str):
            return set(value.split(","))
        elif isinstance(value, set):
            return value
        elif isinstance(value, list):
            return set(value)
        raise ValueError("filter_keys must be a comma-separated string, list, or set.")

    # Custom validator for scheme restriction
    @classmethod
    @field_validator("server_url")
    def validate_scheme(cls, value: Secret[AnyUrl]) -> Secret[AnyUrl]:
        """Validate the URL scheme."""
        if value.get_secret_value().scheme not in {"mqtt", "mqtts"}:
            raise ValueError(
                f"Invalid URL scheme '{value.get_secret_value().scheme}'. Must be 'mqtt' or 'mqtts'."
            )
        return value

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
