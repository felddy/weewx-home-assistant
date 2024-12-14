"""Utility functions and data."""

# Standard Python Libraries
from copy import deepcopy
from datetime import datetime, timezone
from enum import Enum
import logging
import re
from typing import Any, Optional

# Third-Party Libraries
import weewx  # type: ignore
from weewx.units import getStandardUnitType  # type: ignore

logger = logging.getLogger(__name__)


class UnitSystem(str, Enum):
    """Enumeration of unit systems supported by WeeWX.

    Casting to int returns the WeeWX unit system value.
    """

    METRIC = ("METRIC", weewx.METRIC)
    METRICWX = ("METRICWX", weewx.METRICWX)
    US = ("US", weewx.US)

    def __new__(cls, value: str, weewx_value: int):
        """Create a new instance of the enumeration."""
        obj = str.__new__(cls, value)
        obj._value_ = value
        obj.__dict__["_weewx_value"] = (
            weewx_value  # Using __dict__ to set a protected attribute
        )
        return obj

    def __int__(self):
        """Return the WeeWX unit system value."""
        return self._weewx_value

    def __str__(self):
        """Return the unit system value."""
        return self.value

    @classmethod
    def from_int(cls, value: int) -> "UnitSystem":
        """Get the unit system enumeration value from a WeeWX unit system value."""
        for unit_system in cls:
            if int(unit_system) == value:
                return unit_system
        raise ValueError(f"Invalid unit system value: {value}")


def get_unit_metadata(measurement_name: str, unit_system: UnitSystem) -> dict[str, Any]:
    """Generate metadata for a measurement unit based on the unit system."""
    (target_unit, target_group) = getStandardUnitType(
        int(unit_system), measurement_name
    )

    if target_unit is None:
        # take a guess at the unit based on the measurement name
        if measurement_name == "usUnits":
            pass  # Nothing to do for usUnits, this is a special case
        elif measurement_name.endswith("ET"):
            # Map other evapotranspiration measurements (dayET, monthET, yearET) to the same unit as ET
            (target_unit, _) = getStandardUnitType(int(unit_system), "ET")
        elif measurement_name in {"sunrise", "sunset", "stormStart"}:
            (target_unit, _) = getStandardUnitType(int(unit_system), "dateTime")
        else:
            logger.warning(
                "No unit found for measurement '%s' in unit system %s",
                measurement_name,
                unit_system,
            )
        if target_unit:
            logger.info(
                "Guessed unit '%s' for measurement %s", target_unit, measurement_name
            )

    return UNIT_METADATA.get(
        target_unit,
        {"unit_of_measurement": target_unit},  # Defaults to the WeeWX unit if not found
    )


def get_key_config(weewx_key: str) -> dict[str, Any]:
    """Generate metadata for a WeeWX key."""
    # First, attempt an exact match for the key
    config = KEY_CONFIG.get(weewx_key)
    if config:
        return config

    # Next, remove numeric suffix to check for a base key match
    match = re.match(r"(.*?)(\d+)$", weewx_key)
    if match:
        base_key, suffix = match.groups()
        # If the base key is found in the known keys mapping, construct the friendly name
        config = deepcopy(KEY_CONFIG.get(base_key))
        if config:
            config["metadata"]["name"] = f"{config['metadata']['name']} {suffix}"
            return config

    # If we still haven't found a match, generate a friendly name from the key
    # Add space before digits (e.g., extraAlarm5 -> extraAlarm 5)
    key_with_spaces = re.sub(r"(\d+)", r" \1", weewx_key)

    # Split camel case (e.g., extraAlarm 5 -> Extra Alarm 5)
    key_split = re.sub(r"(?<!^)(?=[A-Z])", " ", key_with_spaces).title()

    # Handle "in", "out", "tx", and "rx" prefixes for indoor, outdoor, transmit, and receive
    if key_split.startswith("In "):
        key_split = key_split.replace("In ", "Indoor ", 1)
    elif key_split.startswith("Out "):
        key_split = key_split.replace("Out ", "Outdoor ", 1)
    elif key_split.startswith("Tx "):
        key_split = key_split.replace("Tx ", "Transmit ", 1)
    elif key_split.startswith("Rx "):
        key_split = key_split.replace("Rx ", "Receive ", 1)

    # Guess at what the metadata should be based on the key
    guess: dict[str, Any] = {"metadata": {}}
    if "alarm" in key_split.lower():
        guess = deepcopy(KEY_CONFIG["extraAlarm"])
    elif "battery status" in key_split.lower():
        guess = deepcopy(KEY_CONFIG["batteryStatus"])
    elif "humidity" in key_split.lower():
        guess = deepcopy(KEY_CONFIG["outHumidity"])
    elif "pressure" in key_split.lower():
        guess = deepcopy(KEY_CONFIG["pressure"])
    elif "temperature" in key_split.lower():
        guess = deepcopy(KEY_CONFIG["outTemp"])

    guess["metadata"]["name"] = key_split

    logger.warning("Guessed metadata for key '%s': %s", weewx_key, guess)
    return guess


UNIT_METADATA: dict[str, dict[str, Optional[str]]] = {
    "cm": {"unit_of_measurement": "cm", "value_template": "{{ value | round(2) }}"},
    "degree_C": {
        "unit_of_measurement": "°C",
        "value_template": "{{ value | round(1) }}",
    },
    "degree_F": {
        "unit_of_measurement": "°F",
        "value_template": "{{ value | round(1) }}",
    },
    "degree_K": {
        "unit_of_measurement": "K",
        "value_template": "{{ value | round(1) }}",
    },
    "degree_compass": {
        "unit_of_measurement": "°",
        "value_template": "{{ value | round(0) }}",
    },
    "foot": {"unit_of_measurement": "ft", "value_template": "{{ value | round(2) }}"},
    "gallon": {
        "unit_of_measurement": "gal",
        "value_template": "{{ value | round(2) }}",
    },
    "hPa": {"unit_of_measurement": "hPa", "value_template": "{{ value | round(2) }}"},
    "hour": {"unit_of_measurement": "h", "value_template": "{{ value | round(2) }}"},
    "inHg": {"unit_of_measurement": "inHg", "value_template": "{{ value | round(2) }}"},
    "inch": {"unit_of_measurement": "in", "value_template": "{{ value | round(2) }}"},
    "kPa": {"unit_of_measurement": "kPa", "value_template": "{{ value | round(2) }}"},
    "kilowatt": {
        "unit_of_measurement": "kW",
        "value_template": "{{ value | round(2) }}",
    },
    "kilowatt_hour": {
        "unit_of_measurement": "kWh",
        "value_template": "{{ value | round(2) }}",
    },
    "km_per_hour": {
        "unit_of_measurement": "km/h",
        "value_template": "{{ value | round(1) }}",
    },
    "knot": {"unit_of_measurement": "kn", "value_template": "{{ value | round(1) }}"},
    "liter": {"unit_of_measurement": "L", "value_template": "{{ value | round(2) }}"},
    "lux": {"unit_of_measurement": "lx", "value_template": "{{ value | round(0) }}"},
    "mbar": {"unit_of_measurement": "mbar", "value_template": "{{ value | round(2) }}"},
    "meter": {"unit_of_measurement": "m", "value_template": "{{ value | round(2) }}"},
    "meter_per_second": {
        "unit_of_measurement": "m/s",
        "value_template": "{{ value | round(1) }}",
    },
    "mile_per_hour": {
        "unit_of_measurement": "mph",
        "value_template": "{{ value | round(1) }}",
    },
    "minute": {
        "unit_of_measurement": "min",
        "value_template": "{{ value | round(2) }}",
    },
    "mm": {"unit_of_measurement": "mm", "value_template": "{{ value | round(2) }}"},
    "mmHg": {"unit_of_measurement": "mmHg", "value_template": "{{ value | round(2) }}"},
    "mm_per_hour": {
        "unit_of_measurement": "mm/h",
        "value_template": "{{ value | round(2) }}",
    },
    "percent": {"unit_of_measurement": "%", "value_template": "{{ value | round(0) }}"},
    "percent_battery": {
        "unit_of_measurement": "%",
        "value_template": "{{ value | round(0) }}",
    },
    "second": {"unit_of_measurement": "s", "value_template": "{{ value | round(2) }}"},
    "unix_epoch": {"unit_of_measurement": None},
    "uv_index": {
        "unit_of_measurement": None,
        "value_template": "{{ value | round(0) }}",
    },
    "volt": {"unit_of_measurement": "V", "value_template": "{{ value | round(2) }}"},
    "watt": {"unit_of_measurement": "W", "value_template": "{{ value | round(2) }}"},
    "watt_hour": {
        "unit_of_measurement": "Wh",
        "value_template": "{{ value | round(2) }}",
    },
    "watt_per_meter_squared": {
        "unit_of_measurement": "W/m²",
        "value_template": "{{ value | round(1) }}",
    },
}

KEY_CONFIG: dict[str, Any] = {
    "ET": {
        "metadata": {
            "enabled_by_default": False,
            "icon": "mdi:waves-arrow-up",
            "name": "Evapotranspiration",
        },
    },
    "THSW": {
        "metadata": {
            "icon": "mdi:thermometer-lines",
            "name": "Temperature Humidity Sun Wind Index",
        },
    },
    "UV": {
        "metadata": {"icon": "mdi:sun-wireless", "name": "UV Index"},
    },
    "altimeter": {
        "metadata": {
            "device_class": "atmospheric_pressure",
            "icon": "mdi:altimeter",
            "name": "Pressure Altimeter",
        },
    },
    "altimeterRate": {
        "metadata": {
            "icon": "mdi:altimeter",
            "name": "Altimeter Rate",
        },
    },
    "altitude": {
        "metadata": {
            "device_class": "distance",
            "icon": "mdi:altimeter",
            "name": "Altitude",
        },
    },
    "appTemp": {
        "metadata": {
            "device_class": "temperature",
            "icon": "mdi:thermometer-lines",
            "name": "Apparent Temperature",
        },
    },
    "barometer": {
        "metadata": {
            "device_class": "atmospheric_pressure",
            "icon": "mdi:gauge",
            "name": "Barometric Pressure",
        },
    },
    "barometerRate": {
        "metadata": {
            "icon": "mdi:gauge",
            "name": "Barometric Pressure Rate",
        },
    },
    "batteryStatus": {
        "integration": "binary_sensor",
        "metadata": {
            "device_class": "battery",
            "enabled_by_default": False,
            "icon": "mdi:battery",
            "name": "Battery Status",
            "payload_off": 0,
            "payload_on": 1,
        },
    },
    "beaufort": {
        "metadata": {
            "device_class": "enum",
            "icon": "mdi:windsock",
            "name": "Beaufort Scale",
        },
    },
    "cloudbase": {
        "metadata": {
            "device_class": "distance",
            "icon": "mdi:cloud-arrow-down",
            "name": "Cloud Base Height",
        },
    },
    "cloudcover": {
        "metadata": {
            "icon": "mdi:weather-cloudy-alert",
            "name": "Cloud Cover",
        },
    },
    "co": {
        "metadata": {
            "device_class": "carbon_monoxide",
            "icon": "mdi:molecule-co",
            "name": "Carbon Monoxide",
        },
    },
    "co2": {
        "metadata": {
            "device_class": "carbon_dioxide",
            "icon": "mdi:molecule-co2",
            "name": "Carbon Dioxide",
        },
    },
    "consBatteryVoltage": {
        "metadata": {
            "device_class": "voltage",
            "icon": "mdi:sine-wave",
            "name": "Console Battery Voltage",
        },
    },
    "cooldeg": {
        "metadata": {
            "icon": "mdi:snowflake-thermometer",
            "name": "Cooling Degree Days",
        },
    },
    "dateTime": {
        "convert_lambda": lambda x: datetime.fromtimestamp(
            x, tz=timezone.utc
        ).isoformat(),
        "metadata": {
            "enabled_by_default": False,
            "device_class": "timestamp",
            "icon": "mdi:clock",
            "name": "Date Time",
        },
    },
    "dayET": {
        "metadata": {
            "enabled_by_default": False,
            "icon": "mdi:waves-arrow-up",
            "name": "Day Evapotranspiration",
        },
    },
    "dayRain": {
        "metadata": {
            "device_class": "precipitation",
            "icon": "mdi:cup-water",
            "name": "Day Rainfall",
        },
    },
    "daySunshineDur": {
        "metadata": {
            "device_class": "duration",
            "icon": "mdi:sun-clock",
            "name": "Day Sunshine Duration",
        },
    },
    "dewpoint": {
        "metadata": {
            "device_class": "temperature",
            "icon": "mdi:water-thermometer",
            "name": "Dew Point Temperature",
        },
    },
    "extraAlarm": {
        "integration": "binary_sensor",
        "metadata": {
            "enabled_by_default": False,
            "icon": "mdi:alarm-light",
            "name": "Extra Alarm",
            "payload_off": 0,
            "payload_on": 1,
        },
    },
    "extraHumid": {
        "metadata": {
            "device_class": "humidity",
            "icon": "mdi:water-percent",
            "name": "Extra Humidity",
        },
    },
    "extraTemp": {
        "metadata": {
            "device_class": "temperature",
            "icon": "mdi:thermometer",
            "name": "Extra Temperature",
        },
    },
    "forecastIcon": {
        "metadata": {
            "icon": "mdi:image-frame",
            "name": "Forecast Icon",
        },
    },
    "forecastRule": {
        "metadata": {
            "icon": "mdi:format-list-numbered",
            "name": "Forecast Rule",
        },
    },
    "growdeg": {
        "metadata": {
            "icon": "mdi:sprout",
            "name": "Growing Degree Days",
        },
    },
    "gustdir": {
        "metadata": {
            "icon": "mdi:compass-rose",
            "name": "Wind Gust Direction",
        },
    },
    "hail": {
        "metadata": {
            "device_class": "precipitation",
            "icon": "mdi:weather-hail",
            "name": "Hailfall",
        },
    },
    "hailRate": {
        "metadata": {"icon": "mdi:weather-hail", "name": "Hail Rate"},
    },
    "heatdeg": {
        "metadata": {
            "icon": "mdi:sun-thermometer",
            "name": "Heating Degree Days",
        },
    },
    "heatindex": {
        "metadata": {
            "device_class": "temperature",
            "icon": "mdi:sun-thermometer",
            "name": "Heat Index",
        },
    },
    "heatingTemp": {
        "metadata": {
            "device_class": "temperature",
            "icon": "mdi:sun-thermometer",
            "name": "Heating Temperature",
        },
    },
    "heatingVoltage": {
        "metadata": {
            "device_class": "voltage",
            "icon": "mdi:sine-wave",
            "name": "Heating Voltage",
        },
    },
    "highOutTemp": {
        "metadata": {
            "device_class": "temperature",
            "icon": "mdi:thermometer-high",
            "name": "High Outdoor Temperature",
        },
    },
    "hourRain": {
        "metadata": {
            "device_class": "precipitation",
            "icon": "mdi:cup-water",
            "name": "Hourly Rainfall",
        },
    },
    "humidex": {
        "metadata": {"icon": "mdi:water-percent", "name": "Humidex"},
    },
    "illuminance": {
        "metadata": {
            "device_class": "illuminance",
            "icon": "mdi:sun-wireless",
            "name": "Illuminance",
        },
    },
    "insideAlarm": {
        "integration": "binary_sensor",
        "metadata": {
            "enabled_by_default": False,
            "icon": "mdi:alarm-light",
            "name": "Inside Alarm",
            "payload_off": 0,
            "payload_on": 1,
        },
    },
    "inDewpoint": {
        "metadata": {
            "device_class": "temperature",
            "icon": "mdi:water-thermometer",
            "name": "Indoor Dew Point",
        },
    },
    "inHumidity": {
        "metadata": {
            "device_class": "humidity",
            "icon": "mdi:water-percent",
            "name": "Indoor Humidity",
        },
    },
    "inTemp": {
        "metadata": {
            "device_class": "temperature",
            "icon": "mdi:thermometer",
            "name": "Indoor Temperature",
        },
    },
    "interval": {
        "metadata": {"icon": "mdi:repeat", "name": "Interval"},
    },
    "leafTemp": {
        "metadata": {
            "device_class": "temperature",
            "icon": "mdi:leaf-maple",
            "name": "Leaf Temperature",
        },
    },
    "leafWet": {
        "metadata": {
            "device_class": "moisture",
            "icon": "mdi:leaf-maple",
            "name": "Leaf Wetness",
        },
    },
    "lightning_distance": {
        "metadata": {
            "device_class": "distance",
            "icon": "mdi:flash",
            "name": "Lightning Distance",
        },
    },
    "lightning_disturber_count": {
        "metadata": {
            "icon": "mdi:flash",
            "name": "Lightning Disturber Count",
        },
    },
    "lightning_noise_count": {
        "metadata": {
            "icon": "mdi:flash",
            "name": "Lightning Noise Count",
        },
    },
    "lightning_strike_count": {
        "metadata": {
            "icon": "mdi:flash",
            "name": "Lightning Strike Count",
        },
    },
    "lowOutTemp": {
        "metadata": {
            "device_class": "temperature",
            "icon": "mdi:thermometer-low",
            "name": "Low Outdoor Temperature",
        },
    },
    "maxSolarRad": {
        "metadata": {
            "enabled_by_default": False,
            "device_class": "irradiance",
            "icon": "mdi:sun-wireless",
            "name": "Maximum Solar Radiation",
        },
    },
    "monthET": {
        "metadata": {
            "enabled_by_default": False,
            "icon": "mdi:waves-arrow-up",
            "name": "Month Evapotranspiration",
        },
    },
    "monthRain": {
        "metadata": {
            "device_class": "precipitation",
            "icon": "mdi:cup-water",
            "name": "Monthly Rainfall",
        },
    },
    "nh3": {
        "metadata": {
            "icon": "mdi:chemical-weapon",
            "name": "Ammonia Concentration",
        },
    },
    "no2": {
        "metadata": {
            "device_class": "nitrogen_dioxide",
            "icon": "mdi:chemical-weapon",
            "name": "Nitrogen Dioxide Concentration",
        },
    },
    "noise": {
        "metadata": {
            "device_class": "sound_pressure",
            "icon": "mdi:volume-vibrate",
            "name": "Noise Level",
        },
    },
    "o3": {
        "metadata": {
            "device_class": "ozone",
            "icon": "mdi:chemical-weapon",
            "name": "Ozone Concentration",
        },
    },
    "outHumidity": {
        "metadata": {
            "device_class": "humidity",
            "icon": "mdi:water-percent",
            "name": "Outdoor Humidity",
        },
    },
    "outsideAlarm": {
        "integration": "binary_sensor",
        "metadata": {
            "enabled_by_default": False,
            "icon": "mdi:alarm-light",
            "name": "Outside Alarm",
            "payload_off": 0,
            "payload_on": 1,
        },
    },
    "outTemp": {
        "metadata": {
            "device_class": "temperature",
            "icon": "mdi:thermometer",
            "name": "Outdoor Temperature",
        },
    },
    "outWetbulb": {
        "metadata": {
            "device_class": "temperature",
            "icon": "mdi:thermometer-water",
            "name": "Outdoor Wetbulb Temperature",
        },
    },
    "pb": {
        "metadata": {
            "icon": "mdi:chemical-weapon",
            "name": "Lead Concentration",
        },
    },
    "pm10_0": {
        "metadata": {
            "device_class": "pm10",
            "icon": "mdi:air-filter",
            "name": "PM10 Concentration",
        },
    },
    "pm1_0": {
        "metadata": {
            "device_class": "pm1",
            "icon": "mdi:air-filter",
            "name": "PM1.0 Concentration",
        },
    },
    "pm2_5": {
        "metadata": {
            "device_class": "pm25",
            "icon": "mdi:air-filter",
            "name": "PM2.5 Concentration",
        },
    },
    "pop": {
        "metadata": {
            "icon": "mdi:cloud-percent",
            "name": "Probability of Precipitation",
        },
    },
    "pressure": {
        "metadata": {
            "device_class": "atmospheric_pressure",
            "icon": "mdi:gauge",
            "name": "Atmospheric Pressure",
        },
    },
    "pressureRate": {
        "metadata": {
            "icon": "mdi:gauge",
            "name": "Pressure Rate",
        },
    },
    "radiation": {
        "metadata": {
            "device_class": "irradiance",
            "icon": "mdi:radioactive",
            "name": "Solar Radiation",
        },
    },
    "rain": {
        "metadata": {
            "device_class": "precipitation",
            "icon": "mdi:cup-water",
            "name": "Rainfall",
        },
    },
    "rain24": {
        "metadata": {
            "device_class": "precipitation",
            "icon": "mdi:cup-water",
            "name": "24-Hour Rainfall",
        },
    },
    "rainDur": {
        "metadata": {
            "device_class": "duration",
            "icon": "mdi:timer",
            "name": "Rain Duration",
        },
    },
    "rainRate": {
        "metadata": {
            "device_class": "precipitation_intensity",
            "icon": "mdi:weather-pouring",
            "name": "Rain Rate",
        },
    },
    "referenceVoltage": {
        "metadata": {
            "device_class": "voltage",
            "icon": "mdi:sine-wave",
            "name": "Reference Voltage",
        },
    },
    "rms": {
        "metadata": {
            "device_class": "wind_speed",
            "icon": "mdi:windsock",
            "name": "Root Mean Square Wind Speed",
        },
    },
    "rxCheckPercent": {
        "metadata": {
            "icon": "mdi:radio-tower",
            "name": "Receive Check Percentage",
        },
    },
    "soilLeafAlarm": {
        "integration": "binary_sensor",
        "metadata": {
            "enabled_by_default": False,
            "icon": "mdi:alarm-light",
            "name": "Soil Leaf Alarm",
            "payload_off": 0,
            "payload_on": 1,
        },
    },
    "snow": {
        "metadata": {
            "device_class": "precipitation",
            "icon": "mdi:weather-snowy-heavy",
            "name": "Snowfall",
        },
    },
    "snowDepth": {
        "metadata": {
            "device_class": "distance",
            "icon": "mdi:snowflake",
            "name": "Snow Depth",
        },
    },
    "snowMoisture": {
        "metadata": {
            "device_class": "moisture",
            "icon": "mdi:snowflake-melt",
            "name": "Snow Moisture Content",
        },
    },
    "snowRate": {
        "metadata": {
            "device_class": "precipitation_intensity",
            "icon": "mdi:snowflake",
            "name": "Snow Rate",
        },
    },
    "so2": {
        "metadata": {
            "device_class": "sulphur_dioxide",
            "icon": "mdi:chemical-weapon",
            "name": "Sulfur Dioxide Concentration",
        },
    },
    "soilMoist": {
        "metadata": {
            "device_class": "moisture",
            "icon": "mdi:water-percent",
            "name": "Soil Moisture",
        },
    },
    "soilTemp": {
        "metadata": {
            "device_class": "temperature",
            "icon": "mdi:thermometer",
            "name": "Soil Temperature",
        },
    },
    "stormRain": {
        "metadata": {
            "device_class": "precipitation",
            "icon": "mdi:cup-water",
            "name": "Storm Rainfall",
        },
    },
    "stormStart": {  # is sent in localtime
        "convert_lambda": lambda x: datetime.fromtimestamp(
            x, tz=datetime.now().astimezone().tzinfo
        )
        .astimezone(tz=timezone.utc)
        .isoformat(),
        "metadata": {
            "device_class": "timestamp",
            "icon": "mdi:clock-start",
            "name": "Storm Start Time",
        },
    },
    "sunrise": {  # is sent in localtime
        "convert_lambda": lambda x: datetime.fromtimestamp(
            x, tz=datetime.now().astimezone().tzinfo
        )
        .astimezone(tz=timezone.utc)
        .isoformat(),
        "metadata": {
            "device_class": "timestamp",
            "icon": "mdi:weather-sunset-up",
            "name": "Sunrise",
        },
    },
    "sunset": {  # is sent in localtime
        "convert_lambda": lambda x: datetime.fromtimestamp(
            x, tz=datetime.now().astimezone().tzinfo
        )
        .astimezone(tz=timezone.utc)
        .isoformat(),
        "metadata": {
            "device_class": "timestamp",
            "icon": "mdi:weather-sunset-down",
            "name": "Sunset",
        },
    },
    "sunshineDur": {
        "metadata": {
            "device_class": "duration",
            "icon": "mdi:sun-clock",
            "name": "Sunshine Duration",
        },
    },
    "supplyVoltage": {
        "metadata": {
            "device_class": "voltage",
            "icon": "mdi:sine-wave",
            "name": "Supply Voltage",
        },
    },
    "totalRain": {
        "metadata": {
            "device_class": "precipitation",
            "icon": "mdi:cup-water",
            "name": "Total Rainfall",
        },
    },
    "usUnits": {
        "convert_lambda": lambda x: str(UnitSystem.from_int(x)),
        "metadata": {
            "attributes": {"options": "{{ ['METRIC','METRICWX','US'] }}"},
            "device_class": "enum",
            "icon": "mdi:scale-balance",
            "name": "Units",
        },
    },
    "vecavg": {
        "metadata": {
            "device_class": "wind_speed",
            "icon": "mdi:windsock",
            "name": "Vector Average Wind Speed",
        },
    },
    "vecdir": {
        "metadata": {
            "icon": "mdi:compass-rose",
            "name": "Vector Direction",
        },
    },
    "wind": {
        "metadata": {
            "device_class": "wind_speed",
            "icon": "mdi:windsock",
            "name": "Wind Speed",
        },
    },
    "windDir": {
        "metadata": {
            "icon": "mdi:compass-rose",
            "name": "Wind Direction",
        },
    },
    "windDir10": {
        "metadata": {
            "icon": "mdi:compass-rose",
            "name": "10-Minute Wind Direction",
        },
    },
    "windGust": {
        "metadata": {
            "device_class": "wind_speed",
            "icon": "mdi:windsock",
            "name": "Wind Gust Speed",
        },
    },
    "windGustDir": {
        "metadata": {
            "icon": "mdi:compass-rose",
            "name": "Wind Gust Direction",
        },
    },
    "windSpeed": {
        "metadata": {
            "device_class": "wind_speed",
            "icon": "mdi:windsock",
            "name": "Wind Speed",
        },
    },
    "windSpeed10": {
        "metadata": {
            "device_class": "wind_speed",
            "icon": "mdi:windsock",
            "name": "10-Minute Wind Speed",
        },
    },
    "windchill": {
        "metadata": {
            "device_class": "temperature",
            "icon": "mdi:thermometer",
            "name": "Wind Chill Temperature",
        },
    },
    "windgustvec": {
        "metadata": {
            "device_class": "wind_speed",
            "icon": "mdi:windsock",
            "name": "Wind Gust Vector Speed",
        },
    },
    "windburn": {
        "metadata": {
            "device_class": "distance",
            "icon": "mdi:windsock",
            "name": "Wind Run Distance",
        },
    },
    "windvec": {
        "metadata": {
            "device_class": "wind_speed",
            "icon": "mdi:windsock",
            "name": "Wind Vector Speed",
        },
    },
    "yearET": {
        "metadata": {
            "enabled_by_default": False,
            "icon": "mdi:waves-arrow-up",
            "name": "Year Evapotranspiration",
        },
    },
    "yearRain": {
        "metadata": {
            "device_class": "precipitation",
            "icon": "mdi:cup-water",
            "name": "Yearly Rainfall",
        },
    },
}
