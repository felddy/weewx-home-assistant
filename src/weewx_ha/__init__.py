"""WeeWX extension that publishes to Home Assistant via MQTT."""

# Standard Python Libraries
from importlib.metadata import version

# The version of the installed distribution is the single source of truth,
# defined in pyproject.toml.
__version__ = version("weewx-home-assistant")

# isort is disabled below to prevent circular imports
# isort: off

from .utils import UnitSystem, get_key_config, get_unit_metadata
from .models import ExtensionConfig, MQTTConfig
from .config_publisher import ConfigPublisher
from .state_publisher import StatePublisher
from .preprocessor import PacketPreprocessor
from .controller import Controller

# isort: on

__all__ = [
    "__version__",
    "ConfigPublisher",
    "Controller",
    "ExtensionConfig",
    "get_key_config",
    "get_unit_metadata",
    "MQTTConfig",
    "PacketPreprocessor",
    "StatePublisher",
    "UnitSystem",
]
