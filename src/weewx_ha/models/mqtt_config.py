"""MQTT broker configuration model with optional TLS support."""

# Standard Python Libraries
from typing import Optional

# Third-Party Libraries
from pydantic import BaseModel, ConfigDict, Field, Secret, field_validator

from . import TLSConfig


class MQTTConfig(BaseModel):
    """MQTT broker configuration model."""

    model_config = ConfigDict(
        arbitrary_types_allowed=True, extra="forbid"
    )  # Needed for ssl.SSLContext

    client_id: Optional[str] = None
    hostname: str = Field(..., min_length=1, description="MQTT broker hostname")
    keep_alive: int = Field(
        default=60, ge=0, description="Keep-alive interval in seconds"
    )
    password: Secret[str] = Field(
        ..., description="Password for MQTT broker authentication"
    )
    port: int = Field(
        default=8883, ge=1, le=65535, description="Port number for the MQTT broker"
    )
    qos: int = Field(default=0, ge=0, le=2, description="Quality of Service level")
    tls: TLSConfig = Field(default_factory=TLSConfig, description="TLS configuration")
    username: str = Field(
        ..., min_length=1, description="Username for MQTT broker authentication"
    )
    use_tls: bool = Field(
        default=True, description="Indicates if the connection is secure (uses TLS)"
    )

    @classmethod
    @field_validator("password")
    def validate_password(cls, value: Secret[str]) -> Secret[str]:
        """Ensure that the password is not empty."""
        if not value.get_secret_value():
            raise ValueError("Password cannot be empty.")
        return value
