"""Processes loop packets and publish MQTT discovery configurations."""

# Standard Python Libraries
from collections import defaultdict
import json
import logging
import time
import threading
from typing import Any
from zoneinfo import ZoneInfo

# Third-Party Libraries
import paho.mqtt.client as mqtt
from weewx.units import to_std_system  # type: ignore

# Assuming these are correctly resolved from the weewx-home-assistant project context
from .models import StationInfo
from .utils import UnitSystem, get_key_config, get_unit_metadata

logger = logging.getLogger(__name__)


class ConfigPublisher:
    """Process loop packets and publish MQTT discovery configurations.

    Attributes
    ----------
    availability_topic : str
        The MQTT topic for availability status.
    discovery_topic_prefix : str
        The prefix for MQTT discovery topics.
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
        unit_system : UnitSystem, optional
            The unit system to use for measurements (default is UnitSystem.METRICWX).
        """
        self.availability_topic: str = availability_topic
        self.discovery_topic_prefix: str = discovery_topic_prefix
        self.mqtt_client: mqtt.Client = mqtt_client
        self.node_id: str = node_id
        self.state_topic_prefix: str = state_topic_prefix
        # Store the integer value if UnitSystem is an enum, or the object itself
        # Assuming UnitSystem instances can be cast to int for to_std_system if they are enums.
        # If UnitSystem is just a class with constants, this might need adjustment based on its actual structure.
        self.unit_system_value = int(unit_system) if hasattr(unit_system, 'value') else unit_system


        # Device metadata to include in discovery configurations
        self.device_description: dict[str, Any] = {
            "device": {
                "identifiers": [self.node_id],
                "name": station_info.name,
                "model": station_info.model,
                "manufacturer": station_info.manufacturer,
            }
        }

        self.time_zone: ZoneInfo = station_info.time_zone

        # Dictionary to hold measurement configuration and metadata
        self.seen_measurements: dict[str, dict[str, Any]] = defaultdict(dict)

    def cleanup_old_discovery_topics(self) -> None:
        """
        Clean up old discovery topics before publishing new ones.
        
        This method subscribes to all existing discovery topics for this node,
        collects them, and then deletes them by publishing empty retained messages.
        This ensures that removed sensors don't remain as orphaned entities
        in Home Assistant after a WeeWX restart.
        
        Returns
        -------
        None
        """
        logger.info("Starting cleanup of old discovery topics") # Kept as INFO: Start of a significant operation
        
        discovered_topics = []
        # Event to signal that the subscription has been acknowledged by the broker (SUBACK received)
        subscription_acknowledged = threading.Event()
        
        # --- Temporary Callbacks for Cleanup ---
        def on_discovery_message_cleanup(client, userdata, message, properties=None):
            """Callback to collect existing discovery topics during cleanup."""
            logger.debug(f"Cleanup: Received message on topic: {message.topic}, payload length: {len(message.payload)}")
            if message.payload:  # Only collect non-empty topics (actual configurations)
                if message.topic not in discovered_topics: # Prevent duplicates
                    discovered_topics.append(message.topic)
                    logger.debug(f"Cleanup: Found existing discovery topic to be cleaned: {message.topic}")
                else:
                    logger.debug(f"Cleanup: Topic {message.topic} already in list. Ignoring duplicate.")
            else:
                logger.debug(f"Cleanup: Ignoring empty topic (already cleared or no payload): {message.topic}")
        
        def on_subscribe_cleanup_ack(client, userdata, mid, granted_qos_or_reason_codes, properties=None):
            """Callback after successful subscription acknowledgment for cleanup."""
            logger.debug(f"Cleanup: Subscription acknowledged by broker. QoS/ReasonCodes: {granted_qos_or_reason_codes}.") # Changed to DEBUG
            subscription_acknowledged.set() # Signal that SUBACK was received

        # Store original callbacks to restore them later
        original_on_message = self.mqtt_client.on_message
        original_on_subscribe = self.mqtt_client.on_subscribe
        
        # Set temporary callbacks for cleanup operation
        self.mqtt_client.on_message = on_discovery_message_cleanup
        self.mqtt_client.on_subscribe = on_subscribe_cleanup_ack
        
        cleanup_topic_pattern = f"{self.discovery_topic_prefix}/+/{self.node_id}/+/config"
        logger.debug(f"Cleanup: Subscribing to wildcard pattern: '{cleanup_topic_pattern}' to find all existing topics.") # Changed to DEBUG
        
        result, mid = self.mqtt_client.subscribe(cleanup_topic_pattern, qos=0) 
        
        if result == mqtt.MQTT_ERR_SUCCESS:
            logger.debug(f"Cleanup: Subscription request sent (MID: {mid}). Waiting for SUBACK...") # Changed to DEBUG
            if subscription_acknowledged.wait(timeout=5.0): 
                logger.debug("Cleanup: Subscription active. Waiting for retained messages to arrive...") # Changed to DEBUG
                time.sleep(5.0) 
                logger.info(f"Cleanup: Finished waiting period. Found {len(discovered_topics)} existing discovery topics based on pattern '{cleanup_topic_pattern}'.") # Kept as INFO: Summary is useful
            else:
                logger.warning("Cleanup: Timeout waiting for subscription acknowledgment (SUBACK). Cleanup might be incomplete as retained messages may not have been received.")
        else:
            logger.error(f"Cleanup: Failed to send subscribe request for '{cleanup_topic_pattern}'. Error code: {result}. Cleanup aborted for safety.")
            self.mqtt_client.on_message = original_on_message
            self.mqtt_client.on_subscribe = original_on_subscribe
            logger.info("Cleanup: Restored original MQTT callbacks. Cleanup process halted due to subscription failure.") # Kept as INFO: Important state change
            return 

        logger.debug(f"Cleanup: Unsubscribing from '{cleanup_topic_pattern}'.") # Changed to DEBUG
        self.mqtt_client.unsubscribe(cleanup_topic_pattern)
        
        self.mqtt_client.on_message = original_on_message
        self.mqtt_client.on_subscribe = original_on_subscribe
        logger.debug("Cleanup: Restored original MQTT callbacks.") # Changed to DEBUG

        if discovered_topics:
            logger.info(f"Cleanup: Attempting to delete {len(discovered_topics)} old discovery topics.") # Kept as INFO: Summary of deletion
            for topic in discovered_topics:
                logger.debug(f"Cleanup: Deleting discovery topic by publishing empty retained message: {topic}")
                self.mqtt_client.publish(topic, "", qos=1, retain=True)
            logger.info(f"Cleanup: Deletion messages published for {len(discovered_topics)} old discovery topics.") # Kept as INFO: Confirmation of deletion
        else:
            logger.info("Cleanup: No old discovery topics found to clean up with the current pattern.") # Kept as INFO: Useful to know
        
        logger.info("Discovery topic cleanup completed.") # Kept as INFO: End of a significant operation

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
        logger.debug(f"Processing packet. Unit system value: {self.unit_system_value}")
        found_new_measurements = False
        
        packet_for_processing = packet.copy()

        if self.unit_system_value is not None: 
            try:
                packet_for_processing = to_std_system(packet_for_processing, self.unit_system_value)
            except Exception as e:
                logger.error(f"Error converting packet to standard system: {e}. Using original packet values for discovery.")

        for key in packet_for_processing.keys(): 
            if key not in self.seen_measurements:
                logger.debug(f"Discovered new measurement: {key}") # Changed to DEBUG
                found_new_measurements = True
                
                base_config = get_key_config(key)
                if not isinstance(self.seen_measurements[key], dict): 
                    self.seen_measurements[key] = {}
                self.seen_measurements[key].update(base_config)
                
                unit_meta = get_unit_metadata(key, self.unit_system_value) 
                
                if "metadata" not in self.seen_measurements[key] or not isinstance(self.seen_measurements[key]["metadata"], dict):
                    self.seen_measurements[key]["metadata"] = {}
                self.seen_measurements[key]["metadata"].update(unit_meta)
                
                logger.debug(f"Configuration for new measurement '{key}': {self.seen_measurements[key]}")

        return found_new_measurements

    def publish_discovery(self) -> None:
        """Publish discovery configurations for Home Assistant.

        This method first cleans up any old discovery topics, then publishes 
        MQTT discovery configurations for each sensor in previously seen 
        measurements to allow Home Assistant to automatically discover and 
        configure the sensors.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        logger.info(
            f"Will publish {len(self.seen_measurements)} discovery configurations"
        ) # Kept as INFO
        
        self.cleanup_old_discovery_topics()
        
        logger.info(f"Now publishing {len(self.seen_measurements)} new or updated discovery configurations.") # Kept as INFO
        if not self.seen_measurements:
            logger.info("No measurements seen/processed, so no discovery configurations to publish.") # Kept as INFO
            return

        for sensor_name, config_data in self.seen_measurements.items():
            # sensor_name has the original casing (e.g., "outTemp")

            # For the actual state topic, use the sensor_name with its original casing,
            # just make it safe for MQTT topic (replace spaces, etc.)
            actual_state_topic_suffix = sensor_name.replace(" ", "_").replace("/", "_").replace(".", "_")

            # For Home Assistant entity ID and discovery topic path, use a lowercase, safe version.
            ha_entity_friendly_name = actual_state_topic_suffix.lower()

            integration = config_data.get("integration", "sensor") 
            # Discovery topic path uses the lowercase, HA-friendly name
            discovery_topic = f"{self.discovery_topic_prefix}/{integration}/{self.node_id}/{ha_entity_friendly_name}/config"
            
            payload: dict[str, Any] = {
                "availability_topic": self.availability_topic,
                # State topic in payload must match the actual topic WeeWX publishes to (original case, but MQTT safe)
                "state_topic": f"{self.state_topic_prefix}/{actual_state_topic_suffix}", 
                # Unique ID uses the lowercase, HA-friendly name for consistency in HA entity registry
                "unique_id": f"{self.node_id}_{ha_entity_friendly_name}", 
                "name": config_data.get("metadata", {}).get("name", ha_entity_friendly_name.replace("_", " ").title()),
            }
            
            payload.update(config_data.get("metadata", {}))
            payload.update(self.device_description)

            payload_final = {k: v for k, v in payload.items() if v is not None}

            logger.debug(
                f"Publishing discovery configuration to {discovery_topic}: {json.dumps(payload_final)}"
            ) # Kept as DEBUG
            self.mqtt_client.publish(discovery_topic, json.dumps(payload_final), qos=1, retain=True)
        
        logger.info(f"Finished publishing {len(self.seen_measurements)} discovery configurations.") # Kept as INFO
