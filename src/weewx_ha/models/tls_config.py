"""Defines the sub-model for validating and managing the TLS configuration."""

# Standard Python Libraries
import logging
import ssl
from typing import Any, Optional

# Third-Party Libraries
from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, Secret, model_validator

logger = logging.getLogger(__name__)


class TLSConfig(BaseModel):
    """Pydantic model for secure MQTT TLS configuration defaults."""

    model_config = ConfigDict(extra="forbid")

    cadata: Optional[str] = Field(
        None, description="String containing trusted CA certificates."
    )
    cafile: Optional[str] = Field(
        None, description="Path to a file containing trusted CA certificates."
    )
    capath: Optional[str] = Field(
        None, description="Path to a directory containing trusted CA certificates."
    )
    certfile: Optional[str] = Field(
        None, description="Path to the client certificate file."
    )
    keyfile: Optional[str] = Field(
        None, description="Path to the client private key file."
    )
    password: Optional[Secret[str]] = Field(
        None, description="Password for the client private key file."
    )

    # Define a private attribute for the TLS context
    _context: ssl.SSLContext = PrivateAttr()

    @model_validator(mode="before")
    @classmethod
    def validate_certificate_fields(cls, values: dict[str, Any]) -> dict[str, Any]:
        """Ensure that the certificate and key files are provided together."""
        if values.get("keyfile") and not values.get("certfile"):
            raise ValueError(
                "If 'keyfile' is provided, 'certfile' must also be provided."
            )
        return values

    def __init__(self, **data: Any):
        """Post-initialization customizations.

        More appropriate than in a model_validator as it is creating complex objects.
        """
        super().__init__(**data)
        # We're going to trust the maintainers of the default context to keep our
        # security settings sane and up-to-date.
        self._context = ssl.create_default_context(
            purpose=ssl.Purpose.SERVER_AUTH,
            cafile=self.cafile,
            capath=self.capath,
            cadata=self.cadata,
        )

        if self.certfile and self.keyfile:
            #  Load client certificate and key files.
            logger.debug("Loading client certificate and key files into SSL context.")
            self._context.load_cert_chain(
                certfile=self.certfile,
                keyfile=self.keyfile,
                password=(self.password.get_secret_value() if self.password else None),
            )

    @property
    def context(self) -> ssl.SSLContext:
        """Provide access to the computed TLS context."""
        return self._context
