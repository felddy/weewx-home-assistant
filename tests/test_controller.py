#!/usr/bin/env pytest -vs
"""Tests for the Controller's MQTT startup ordering.

paho may invoke callbacks on its network thread the instant connect()
is called. The fake client below simulates the fastest legal broker by
delivering CONNACK and a retained ``homeassistant/status: online``
birth message synchronously inside connect(), turning the startup race
into a deterministic check: if the controller connects before the
attributes its callbacks use exist, construction raises
AttributeError ('Controller' object has no attribute 'executor').
"""

# Standard Python Libraries
from types import SimpleNamespace
from unittest.mock import MagicMock

# Geekpad Libraries
from weewx_ha import controller as controller_module

CONFIG_DICT = {
    "HomeAssistant": {
        "mqtt": {
            "hostname": "broker.test",
            "password": "test-fixture-not-a-secret",  # nosec
            "use_tls": False,
            "username": "weewx",
        },
        "node_id": "test_station",
        "station": {
            "name": "Test Station",
            "model": "T-1000",
            "manufacturer": "ACME",
        },
    }
}


class InstantBrokerClient:
    """mqtt.Client stand-in for a zero-latency broker.

    connect() runs the CONNACK callback and then delivers the retained
    Home Assistant birth message that the on_connect subscription just
    matched — synchronously, the worst callback timing paho permits.
    """

    def __init__(self, *args, **kwargs):
        """Accept the mqtt.Client constructor signature."""
        self.logger = None
        self.on_connect = None
        self.on_connect_fail = None
        self.on_disconnect = None
        self.on_message = None
        self.on_subscribe = None
        self.on_unsubscribe = None
        self.published: list[tuple[str, object]] = []
        self.subscribed: list[str] = []

    def loop_start(self):
        """Pretend to start the network thread."""

    def will_set(self, topic, payload=None, qos=0, retain=False):
        """Accept the last will."""

    def username_pw_set(self, username, password=None):
        """Accept credentials."""

    def tls_set_context(self, context=None):
        """Accept a TLS context."""

    def publish(self, topic, payload=None, qos=0, retain=False):
        """Record a publish."""
        self.published.append((topic, payload))

    def subscribe(self, topic, qos=0):
        """Record a subscription."""
        self.subscribed.append(topic)

    def connect(self, host, port=1883, keepalive=60):
        """Deliver CONNACK and the retained birth message synchronously."""
        self.on_connect(self, None, {}, 0, None)
        message = SimpleNamespace(topic="homeassistant/status", payload=b"online")
        self.on_message(self, None, message)


def test_mqtt_callbacks_cannot_outrun_initialization(monkeypatch):
    """A zero-latency broker must never observe a half-built controller."""
    monkeypatch.setattr(controller_module.mqtt, "Client", InstantBrokerClient)
    publish_discovery = MagicMock()
    monkeypatch.setattr(
        controller_module.ConfigPublisher, "publish_discovery", publish_discovery
    )

    controller = controller_module.Controller(MagicMock(), dict(CONFIG_DICT))

    # The connect handshake ran: availability published, birth topic subscribed.
    assert (controller.availability_topic, "online") in controller.mqtt_client.published
    assert "homeassistant/status" in controller.mqtt_client.subscribed
    # The birth message dispatched a discovery publish through the executor.
    controller.executor.shutdown(wait=True)
    publish_discovery.assert_called_once()
