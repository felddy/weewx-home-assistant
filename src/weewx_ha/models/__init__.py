"""This module initializes the models package and imports the necessary configuration classes."""

from .extension_config import ExtensionConfig
from .mqtt_config import MQTTConfig

__all__ = ["ExtensionConfig", "MQTTConfig"]
