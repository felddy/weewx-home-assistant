"""MQTT broker configuration model with optional TLS support."""

# Standard Python Libraries
import ssl
from typing import Optional
from urllib.parse import parse_qs

# Third-Party Libraries
from pydantic import AnyUrl, BaseModel, ConfigDict, Field, Secret, model_validator


class MQTTConfig(BaseModel):
    """MQTT broker configuration model."""

    model_config = ConfigDict(
        arbitrary_types_allowed=True, extra="forbid"
    )  # Needed for ssl.SSLContext

    client_id: Optional[str] = None
    hostname: str = Field(..., min_length=1, description="MQTT broker hostname")
    is_secure: bool = Field(
        description="Indicates if the connection is secure (uses TLS)"
    )
    keep_alive: int = Field(
        default=60, ge=0, description="Keep-alive interval in seconds"
    )
    password: Optional[Secret[str]] = Field(
        description="Password for MQTT broker authentication"
    )
    port: int = Field(ge=1, le=65535, description="Port number for the MQTT broker")
    qos: int = Field(default=0, ge=0, le=2, description="Quality of Service level")
    tls: Optional[ssl.SSLContext] = None
    username: Optional[str] = Field(
        min_length=1, description="Username for MQTT broker authentication"
    )

    @model_validator(mode="after")
    def set_tls(cls, values):
        """Set the default TLS context if the connection is secure and no context is provided."""
        if values.is_secure and values.tls is None:
            values.tls = ssl.create_default_context()
            values.tls.load_default_certs()  # Load default CA certificates
        return values

    @classmethod
    def from_url(cls, url: AnyUrl) -> "MQTTConfig":
        """Create an MQTTConfig instance from an MQTT broker URL."""
        if url.scheme not in ["mqtt", "mqtts"]:
            raise ValueError("Unsupported URL scheme. Must be 'mqtt' or 'mqtts'.")

        # Extract components
        is_secure = url.scheme == "mqtts"
        hostname = url.host
        port = url.port if url.port else (8883 if is_secure else 1883)
        username = url.username
        password = url.password
        query_params = parse_qs(url.query)

        # Handling query parameters
        client_id = query_params.get("client_id", [None])[
            0
        ]  # Extract client_id if available
        keep_alive = int(
            query_params.get("keep_alive", [60])[0]
        )  # Default keep_alive is 60 seconds
        qos = int(query_params.get("qos", [0])[0])  # Default QoS is 0

        # Creating the MQTTConfig instance
        return cls(
            client_id=client_id,
            hostname=hostname,
            is_secure=is_secure,
            keep_alive=keep_alive,
            password=Secret(password) if password is not None else None,
            port=port,
            qos=qos,
            username=username,
        )
