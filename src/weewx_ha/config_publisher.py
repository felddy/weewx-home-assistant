"""Processes loop packets and publish MQTT discovery configurations."""

# Standard Python Libraries
from collections import defaultdict
import json
import logging
from typing import Any

# Third-Party Libraries
import paho.mqtt.client as mqtt
from weewx.units import to_std_system  # type: ignore

from .models import StationInfo
from .utils import UnitSystem, get_key_metadata, get_unit_metadata

logger = logging.getLogger(__name__)


class ConfigPublisher:
    """Process loop packets and publish MQTT discovery configurations.

    Attributes
    ----------
    availability_topic : str
        The MQTT topic for availability status.
    discovery_topic_prefix : str
        The prefix for MQTT discovery topics.
    filter_keys : set of str
        A set of keys to filter the measurements.
    mqtt_client : mqtt.Client
        The MQTT client used for publishing messages.
    node_id : str
        The unique identifier for the node.
    state_topic_prefix : str
        The prefix for MQTT state topics.
    unit_system : UnitSystem
        The unit system to use for measurements.
    seen_measurements : dict of str to dict of str to Any
        A dictionary to hold measurement metadata.
    """

    def __init__(
        self,
        mqtt_client: mqtt.Client,
        availability_topic: str,
        discovery_topic_prefix: str,
        state_topic_prefix: str,
        node_id: str,
        station_info: StationInfo,
        filter_keys: set[str],
        unit_system: UnitSystem = UnitSystem.METRICWX,
    ):
        """
        Initialize the ConfigPublisher.

        Parameters
        ----------
        mqtt_client : mqtt.Client
            The MQTT client used for publishing messages.
        availability_topic : str
            The MQTT topic for availability status.
        discovery_topic_prefix : str
            The prefix for MQTT discovery topics.
        state_topic_prefix : str
            The prefix for MQTT state topics.
        node_id : str
            The unique identifier for the node.
        station_info : StationInfo
            The weather station information.
        filter_keys : set of str
            A set of keys to filter the measurements.
        unit_system : UnitSystem, optional
            The unit system to use for measurements (default is UnitSystem.METRICWX).
        """
        self.availability_topic: str = availability_topic
        self.discovery_topic_prefix: str = discovery_topic_prefix
        self.filter_keys: set[str] = filter_keys or set()
        self.mqtt_client: mqtt.Client = mqtt_client
        self.node_id: str = node_id
        self.state_topic_prefix: str = state_topic_prefix
        self.unit_system: UnitSystem = unit_system

        # Device metadata to include in discovery configurations
        self.device_description: dict[str, Any] = {
            "device": {
                "identifiers": [self.node_id],
                "name": station_info.name,
                "model": station_info.model,
                "manufacturer": station_info.manufacturer,
            }
        }

        # Dictionary to hold measurement metadata
        self.seen_measurements: dict[str, dict[str, Any]] = defaultdict(dict)

    def process_packet(self, packet: dict) -> bool:
        """
        Process packet and compose discovery configurations.

        Parameters
        ----------
        packet : dict
            The packet of measurements to process.

        Returns
        -------
        bool
            True if new measurements were discovered, False otherwise.

        """
        logger.debug("Processing packet")
        found_new_measurements = False
        if self.unit_system is not None:
            packet = to_std_system(packet, int(self.unit_system))
        for key in packet.keys():
            if key in self.filter_keys:
                continue
            if key not in self.seen_measurements:
                logger.debug(f"Discovered new measurement: {key}")
                found_new_measurements = True
                self.seen_measurements[key] |= get_unit_metadata(key, self.unit_system)
                self.seen_measurements[key] |= get_key_metadata(key)
        return found_new_measurements

    def publish_discovery(self) -> None:
        """Publish discovery configurations for Home Assistant.

        This method publishes MQTT discovery configurations for each sensor
        in previously seen measurements to allow Home Assistant to automatically
        discover and configure the sensors.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        logger.info(
            f"Publishing {len(self.seen_measurements)} discovery configurations"
        )
        for sensor_name, metadata in self.seen_measurements.items():
            # Construct discovery topic
            discovery_topic = f"{self.discovery_topic_prefix}/sensor/{self.node_id}/{sensor_name}/config"
            # Construct the configuration payload
            payload: dict[str, Any] = (
                {
                    "availability_topic": self.availability_topic,
                    "state_topic": f"{self.state_topic_prefix}/{sensor_name}",
                    "unique_id": f"{self.node_id}_{sensor_name}",
                }
                | metadata
                | self.device_description
            )

            # Remove any keys with None values
            payload = {k: v for k, v in payload.items() if v is not None}

            logger.debug(
                f"Publishing discovery configuration: {discovery_topic}: {payload}"
            )
            # Publish the discovery configuration
            self.mqtt_client.publish(discovery_topic, json.dumps(payload))
