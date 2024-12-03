"""
Integrates WeeWX with Home Assistant via MQTT.

This module defines the Controller class. The Controller class extends the
StdService class from WeeWX and manages the MQTT client, publishes state and
configuration data, and handles WeeWX loop packets.
"""

# Standard Python Libraries
from concurrent.futures import ThreadPoolExecutor
import logging
from typing import Any

# Third-Party Libraries
import paho.mqtt.client as mqtt
from weewx import NEW_LOOP_PACKET  # type: ignore
from weewx.engine import StdEngine, StdService  # type: ignore

from . import ConfigPublisher, StatePublisher
from .models import ExtensionConfig, MQTTConfig

logger = logging.getLogger(__name__)

# TODO Add command topics to control configuration settings

# Constants
EXTENSION_CONFIG_KEY = "HAMQTT"
THREAD_POOL_SIZE = 2


class Controller(StdService):
    """Controller class for the Home Assistant MQTT extension."""

    def __init__(self, engine: StdEngine, config_dict: dict[Any, Any]):
        """Initialize the controller.

        Args:
            engine: The WeeWX engine
            config_dict: The configuration dictionary
        """
        super().__init__(engine, config_dict)
        logger.debug(
            f"Initializing extension with configuration key {EXTENSION_CONFIG_KEY}"
        )
        try:
            self.config = ExtensionConfig.from_config_dict(
                config_dict, EXTENSION_CONFIG_KEY
            )
        except Exception:
            logger.error(
                "Invalid or missing extension configuration. Extension will not be loaded.",
                exc_info=True,
            )
            return
        logger.debug(
            f"Loaded extension configuration:\n{self.config.model_dump_json(indent=4)}"
        )

        self.availability_topic: str = f"{self.config.state_topic_prefix}/status"
        self.mqtt_client: mqtt.Client = self.init_mqtt_client(self.config.mqtt)

        # Thread pool for managing publisher tasks
        self.executor = ThreadPoolExecutor(max_workers=THREAD_POOL_SIZE)

        # Create a publishers
        self.state_publisher = StatePublisher(
            self.mqtt_client,
            self.config.state_topic_prefix,
            self.config.filter_keys,
            self.config.unit_system,
        )
        self.config_publisher = ConfigPublisher(
            self.mqtt_client,
            self.availability_topic,
            self.config.discovery_topic_prefix,
            self.config.state_topic_prefix,
            self.config.node_id,
            self.config.station,
            self.config.filter_keys,
            self.config.unit_system,
        )

        # Register the callbacks for loop packets
        self.bind(NEW_LOOP_PACKET, self.on_weewx_loop)

    def init_mqtt_client(self, mqtt_config: MQTTConfig):
        """Initialize the MQTT client."""
        logger.info(f"MQTT configuration: {mqtt_config}")
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, mqtt_config.client_id)
        client.logger = logger
        # Set the callbacks
        client.on_connect = self.on_mqtt_connect
        client.on_message = self.on_mqtt_message
        client.on_subscribe = self.on_mqtt_subscribe
        client.on_unsubscribe = self.on_mqtt_unsubscribe
        client.on_disconnect = self.on_mqtt_disconnect
        if mqtt_config.use_tls:
            client.tls_set_context(mqtt_config.tls.context)
        if mqtt_config.username and mqtt_config.password:
            client.username_pw_set(
                mqtt_config.username, mqtt_config.password.get_secret_value()
            )
        client.loop_start()
        # Set the last will and testament
        client.will_set(self.availability_topic, "offline", retain=True)
        client.connect(mqtt_config.hostname, mqtt_config.port, mqtt_config.keep_alive)
        return client

    def on_mqtt_connect(
        self, client: mqtt.Client, userdata, flags, reason_code, properties
    ):
        """Handle callback when the client attempts to connect to the server."""
        if reason_code == 0:
            logger.info("Connected to MQTT broker")
            logger.info("Publishing online availability")
            # Send our birth message
            client.publish(self.availability_topic, "online", retain=True)
            # Subscribe to the homeassistant birth message
            client.subscribe(f"{self.config.discovery_topic_prefix}/status")
        else:
            logger.error(f"Failed to connect to MQTT broker, return code {reason_code}")

    def on_mqtt_connect_fail(self, client: mqtt.Client, userdata):
        """Handle callback when the client fails to connect to the server."""
        logger.error("Failed to connect to MQTT broker")

    def on_mqtt_disconnect(
        self, client: mqtt.Client, userdata, disconnect_flags, reason_code, properties
    ):
        """Handle callback for when the client disconnects from the server."""
        if reason_code != 0:
            logger.warning(
                f"Unexpected disconnection from MQTT broker, return code {reason_code}, disconnect flags {disconnect_flags}"
            )
        else:
            logger.info("Disconnected from MQTT broker")

    def on_mqtt_message(self, client: mqtt.Client, userdata, msg):
        """Handle callback for when a PUBLISH message is received from the server."""
        logger.info(f"Received message on topic {msg.topic}: {msg.payload}")
        # Resend config on homeassistant birth
        if (
            msg.topic == f"{self.config.discovery_topic_prefix}/status"
            and msg.payload == b"online"
        ):
            future = self.executor.submit(self.config_publisher.publish_discovery)
            future.add_done_callback(self.check_future_result)

    def on_mqtt_subscribe(
        self, client: mqtt.Client, userdata, mid, reason_code_list, properties
    ):
        """Handle callback for when the broker responds to a subscribe request."""
        logger.info(f"Subscribed to topic, message ID: {mid}")

    def on_mqtt_unsubscribe(
        self, client: mqtt.Client, userdata, mid, reason_code_list, properties
    ):
        """Handle callback for when the broker responds to an unsubscribe request."""
        logger.info(f"Unsubscribed from topic, message ID: {mid}")

    def check_future_result(self, future):
        """Handle callback and check for exceptions in a Future."""
        try:
            future.result()
        except Exception as e:
            logger.error(f"Error in future: {e}", exc_info=True)

    def on_weewx_loop(self, event):
        """Handle callback for WeeWX loop packets."""
        logger.debug("Received WeeWX loop packet")
        if self.mqtt_client.is_connected():
            state_future = self.executor.submit(
                self.state_publisher.process_packet, event.packet
            )
            state_future.add_done_callback(self.check_future_result)
            config_future = self.executor.submit(
                self.config_publisher.process_packet, event.packet
            )

            def check_config_update(future):
                try:
                    # Get the result of the Future, which will be True or False
                    needs_publish = future.result()
                    if needs_publish:
                        logger.debug(
                            "New measurements found, submitting config update task"
                        )
                        future2 = self.executor.submit(
                            self.config_publisher.publish_discovery
                        )
                        future2.add_done_callback(self.check_future_result)
                except Exception as e:
                    logger.error(
                        f"Error while checking config update: {e}", exc_info=True
                    )

            # Add callback to config processing task
            config_future.add_done_callback(check_config_update)
        else:
            logger.warning("MQTT client is not connected, skipping packet processing")

    def shutDown(self):
        """Shutdown the controller.

        This method is overrides the method in StdService class and is called when the extension is unloaded.
        """
        logger.warning("Shutdown requested")

        logger.info("Publishing offline availability")
        self.mqtt_client.publish(self.availability_topic, "offline", retain=True)

        # Shutdown the executor, allowing threads to complete pending work
        self.executor.shutdown(wait=True)
        self.mqtt_client.disconnect()  # Also stops the MQTT client loop
        logger.info("All publisher tasks shut down gracefully.")
