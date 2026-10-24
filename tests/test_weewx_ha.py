#!/usr/bin/env pytest -vs
"""Tests for weewx_ha."""

# Standard Python Libraries
import json
import logging
import os
from unittest.mock import MagicMock

# Third-Party Libraries
import pytest
import weewx

# Geekpad Libraries
import weewx_ha
from weewx_ha import (
    ConfigPublisher,
    ExtensionConfig,
    StatePublisher,
    UnitSystem,
    get_unit_metadata,
)
from weewx_ha.models import StationInfo
from weewx_ha.utils import KEY_CONFIG

# define sources of version strings
RELEASE_TAG = os.getenv("RELEASE_TAG")
PROJECT_VERSION = weewx_ha.__version__


@pytest.mark.skipif(
    RELEASE_TAG in [None, ""], reason="this is not a release (RELEASE_TAG not set)"
)
def test_release_version():
    """Verify that release tag version agrees with the module version."""
    assert (
        RELEASE_TAG == f"v{PROJECT_VERSION}"
    ), "RELEASE_TAG does not match the project version"


TEST_PACKET = {
    "usUnits": weewx.METRICWX,
    "outTemp": 20.0,
    "dayRain": 1.2,
    "windDir": 180.0,
}


def make_config_publisher(retain: bool = False) -> ConfigPublisher:
    """Create a ConfigPublisher with a mocked MQTT client."""
    return ConfigPublisher(
        MagicMock(),
        "weather/status",
        "homeassistant",
        "weather",
        "testnode",
        StationInfo(name="Test Station", model="Test Model", manufacturer="Test"),
        UnitSystem.METRICWX,
        retain=retain,
    )


def discovery_payloads(publisher: ConfigPublisher) -> dict:
    """Publish discovery and return payloads indexed by topic."""
    publisher.publish_discovery()
    return {
        call.args[0]: json.loads(call.args[1])
        for call in publisher.mqtt_client.publish.call_args_list
    }


def test_discovery_state_class():
    """Verify state_class is set appropriately in discovery configurations."""
    publisher = make_config_publisher()
    assert publisher.process_packet(dict(TEST_PACKET)) is True
    payloads = discovery_payloads(publisher)
    assert (
        payloads["homeassistant/sensor/testnode/outTemp/config"]["state_class"]
        == "measurement"
    )
    assert (
        payloads["homeassistant/sensor/testnode/dayRain/config"]["state_class"]
        == "total_increasing"
    )
    # Circular quantities must not have a state_class
    assert "state_class" not in payloads["homeassistant/sensor/testnode/windDir/config"]


@pytest.mark.parametrize("retain", [False, True])
def test_discovery_retain(retain):
    """Verify discovery configurations are published with the configured retain flag."""
    publisher = make_config_publisher(retain=retain)
    publisher.process_packet(dict(TEST_PACKET))
    publisher.publish_discovery()
    calls = publisher.mqtt_client.publish.call_args_list
    assert calls, "expected discovery publications"
    assert all(call.kwargs["retain"] is retain for call in calls)


@pytest.mark.parametrize("retain", [False, True])
def test_state_retain(retain):
    """Verify state updates are published with the configured retain flag."""
    config_publisher = make_config_publisher()
    config_publisher.process_packet(dict(TEST_PACKET))
    client = MagicMock()
    publisher = StatePublisher(
        client, config_publisher, "weather", UnitSystem.METRICWX, retain=retain
    )
    publisher.process_packet(dict(TEST_PACKET))
    calls = client.publish.call_args_list
    assert calls, "expected state publications"
    assert all(call.kwargs["retain"] is retain for call in calls)


def test_extension_config_retain_defaults_and_coercion():
    """Verify retain options default to False and coerce config strings."""
    base = {
        "node_id": "testnode",
        "mqtt": {"hostname": "mqtt.example.com", "username": "u", "password": "p"},
        "station": {"name": "Test", "model": "Model", "manufacturer": "Maker"},
    }
    config = ExtensionConfig(**base)
    assert config.retain_discovery is False
    assert config.retain_state is False
    # WeeWX config values arrive as strings
    config = ExtensionConfig(**base, retain_discovery="true", retain_state="false")
    assert config.retain_discovery is True
    assert config.retain_state is False


@pytest.mark.parametrize(
    "key,unit_system,expected",
    [
        ("rainRate", UnitSystem.US, "in/h"),
        ("rainRate", UnitSystem.METRIC, "cm/h"),
        ("rainRate", UnitSystem.METRICWX, "mm/h"),
        ("barometerRate", UnitSystem.US, "inHg/h"),
        ("barometerRate", UnitSystem.METRICWX, "mbar/h"),
    ],
)
def test_rate_unit_metadata(key, unit_system, expected):
    """Verify rate measurements resolve to known unit metadata in every unit system."""
    metadata = get_unit_metadata(key, unit_system)
    assert metadata["unit_of_measurement"] == expected
    assert "value_template" in metadata


def test_seen_measurements_fully_built():
    """Verify configurations are complete as soon as they appear in seen_measurements."""
    publisher = make_config_publisher()
    publisher.process_packet(dict(TEST_PACKET))
    for key, config in publisher.seen_measurements.items():
        assert "metadata" in config, f"{key} missing metadata"
        assert "name" in config["metadata"], f"{key} missing name"


def test_key_config_not_mutated_by_processing():
    """Verify processing packets does not leak unit metadata into KEY_CONFIG."""
    publisher = make_config_publisher()
    publisher.process_packet(dict(TEST_PACKET))
    assert "unit_of_measurement" not in KEY_CONFIG["outTemp"]["metadata"]


@pytest.mark.parametrize("key", ["dateTime", "stormStart", "sunrise", "sunset"])
def test_timestamp_conversion_is_utc(key):
    """Verify timestamp keys convert Unix epochs directly to UTC ISO 8601."""
    epoch = 1700000000  # 2023-11-14T22:13:20+00:00
    convert = KEY_CONFIG[key]["convert_lambda"]
    assert convert(epoch, None) == "2023-11-14T22:13:20+00:00"


def test_time_zone_deprecation_warning(caplog):
    """Verify a warning is logged only when the deprecated time_zone is set."""
    base = {"name": "Test", "model": "Model", "manufacturer": "Maker"}
    with caplog.at_level(logging.WARNING):
        StationInfo(**base)
    assert "deprecated" not in caplog.text
    with caplog.at_level(logging.WARNING):
        StationInfo(**base, time_zone="America/New_York")
    assert "time_zone" in caplog.text
    assert "deprecated" in caplog.text


def test_windrun_key_config():
    """Verify windrun (not windburn) resolves to the wind run metadata."""
    config = weewx_ha.get_key_config("windrun")
    assert config["metadata"]["name"] == "Wind Run Distance"
    assert config["metadata"]["state_class"] == "total_increasing"
    assert "windburn" not in KEY_CONFIG


def test_rain_alarm_key_config():
    """Verify rainAlarm has an explicit binary sensor configuration."""
    config = weewx_ha.get_key_config("rainAlarm")
    assert config["integration"] == "binary_sensor"
    assert config["metadata"]["name"] == "Rain Alarm"


def test_no_unit_warnings_for_unitless_keys(caplog):
    """Verify unit-less measurements are processed without unit warnings."""
    publisher = make_config_publisher()
    packet = {
        "usUnits": weewx.METRICWX,
        "batteryStatusISS": 0,
        "extraAlarm1": 0,
        "forecastIcon": 8,
        "forecastRule": 45,
        "insideAlarm": 0,
        "rainAlarm": 0,
        "soilLeafAlarm4": 0,
        "windrun": 12.3,
    }
    with caplog.at_level(logging.INFO):
        publisher.process_packet(packet)
    assert "No unit found" not in caplog.text
    assert "Guessed metadata" not in caplog.text
    # The unitless marker must not leak into published configurations
    assert "unitless" not in publisher.seen_measurements["forecastIcon"]


def test_unit_warning_remains_for_unknown_numeric_keys(caplog):
    """Verify genuinely unmapped measurements still warn about missing units."""
    publisher = make_config_publisher()
    with caplog.at_level(logging.WARNING):
        publisher.process_packet({"usUnits": weewx.METRICWX, "mysteryReading": 1.0})
    assert "No unit found" in caplog.text
