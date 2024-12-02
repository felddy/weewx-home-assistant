"""MQTT broker configuration model with optional TLS support."""

# Standard Python Libraries
import ssl
from typing import Any, Optional

# Third-Party Libraries
from pydantic import BaseModel, ConfigDict, Field, Secret, field_validator


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
    tls: Optional[ssl.SSLContext] = None  # will be set in __post_init_post_parse__
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

    def __init__(self, **data: Any):
        """Post-initialization customizations.

        More appropriate than in a model_validator as it is creating complex objects.
        """
        super().__init__(**data)
        # Set the TLS context after model initialization if necessary
        if self.use_tls and self.tls is None:
            self.tls = ssl.create_default_context()
            self.tls.load_default_certs()  # Load default CA certificates
