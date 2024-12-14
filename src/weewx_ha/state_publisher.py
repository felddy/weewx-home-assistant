"""Processes loop packets and publish state to MQTT."""

# Standard Python Libraries
from datetime import datetime, timezone
import logging

# Third-Party Libraries
import paho.mqtt.client as mqtt
from weewx.units import to_std_system  # type: ignore

from . import UnitSystem

logger = logging.getLogger(__name__)

DATETIME_KEYS = {"dateTime", "stormStart", "sunrise", "sunset"}


class StatePublisher:
    """Process loop packets and publish state to MQTT.

    Attributes
    ----------
    mqtt_client : mqtt.Client
        The MQTT client used for publishing state updates.
    state_topic_prefix : str
        The prefix for the MQTT topic where state updates will be published.
    unit_system : UnitSystem
        The unit system to use for the state updates.
    """

    def __init__(
        self,
        mqtt_client: mqtt.Client,
        state_topic_prefix: str,
        unit_system: UnitSystem = UnitSystem.METRICWX,
    ):
        """
        Initialize the publisher.

        Parameters
        ----------
        mqtt_client : mqtt.Client
            The MQTT client used for publishing state updates.
        state_topic_prefix : str
            The prefix for the MQTT topic where state updates will be published.
        unit_system : UnitSystem, optional
            The unit system to use for the state updates. Default is UnitSystem.METRICWX.
        """
        self.mqtt_client = mqtt_client
        self.state_topic_prefix = state_topic_prefix
        self.unit_system = unit_system

    def process_packet(self, packet: dict) -> None:
        """Process record and publish to MQTT."""
        logger.debug("Processing packet")
        if self.unit_system is not None:
            packet = to_std_system(packet, int(self.unit_system))
        for key, value in packet.items():
            if value is None:
                # Publishing None values angers Home Assistant when processing templates
                continue
            if key in DATETIME_KEYS:
                value = datetime.fromtimestamp(value, tz=timezone.utc).isoformat()
            elif key == "usUnits":
                value = str(UnitSystem.from_int(value))
            self.mqtt_client.publish(f"{self.state_topic_prefix}/{key}", value)
