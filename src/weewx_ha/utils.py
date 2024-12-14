"""Utility functions and data."""

# Standard Python Libraries
from copy import copy
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
        if "battery" in measurement_name.lower():
            target_unit = "percent_battery"
        elif measurement_name == "usUnits":
            pass  # Nothing to do for usUnits, but not a warning either
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


def get_key_metadata(weewx_key: str) -> dict[str, Any]:
    """Generate metadata for a WeeWX key."""
    # First, attempt an exact match for the key
    metadata = KEY_METADATA.get(weewx_key)
    if metadata:
        return metadata

    # Next, remove numeric suffix to check for a base key match
    match = re.match(r"(.*?)(\d+)$", weewx_key)
    if match:
        base_key, suffix = match.groups()
        # If the base key is found in the known keys mapping, construct the friendly name
        metadata = copy(KEY_METADATA.get(base_key))
        if metadata:
            metadata["name"] = f"{metadata['name']} {suffix}"
            return metadata

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

    # Guess at an icon and class
    guess: dict[str, bool | str] = {"name": key_split}
    if "alarm" in key_split.lower():
        guess["icon"] = "mdi:alarm-light"
        guess["enabled_by_default"] = False
    elif "battery" in key_split.lower():
        guess["device_class"] = "battery"
        guess["icon"] = "mdi:battery-outline"
    elif "humidity" in key_split.lower():
        guess["device_class"] = "humidity"
        guess["icon"] = "mdi:water-percent"
    elif "pressure" in key_split.lower():
        guess["device_class"] = "pressure"
        guess["icon"] = "mdi:gauge"
    elif "temperature" in key_split.lower():
        guess["device_class"] = "temperature"
        guess["icon"] = "mdi:thermometer"
    elif "wind" in key_split.lower():
        guess["device_class"] = "wind_speed"
        guess["icon"] = "mdi:windsock"

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

KEY_METADATA: dict[str, dict[str, Optional[bool | dict | str]]] = {
    "ET": {
        "enabled_by_default": False,
        "icon": "mdi:waves-arrow-up",
        "name": "Evapotranspiration",
    },
    "THSW": {
        "icon": "mdi:thermometer-lines",
        "name": "Temperature Humidity Sun Wind Index",
    },
    "UV": {"icon": "mdi:sun-wireless", "name": "UV Index"},
    "altimeter": {
        "device_class": "atmospheric_pressure",
        "icon": "mdi:altimeter",
        "name": "Pressure Altimeter",
    },
    "altimeterRate": {
        "icon": "mdi:altimeter",
        "name": "Altimeter Rate",
    },
    "altitude": {
        "device_class": "distance",
        "icon": "mdi:altimeter",
        "name": "Altitude",
    },
    "appTemp": {
        "device_class": "temperature",
        "icon": "mdi:thermometer-lines",
        "name": "Apparent Temperature",
    },
    "barometer": {
        "device_class": "atmospheric_pressure",
        "icon": "mdi:gauge",
        "name": "Barometric Pressure",
    },
    "barometerRate": {
        "icon": "mdi:gauge",
        "name": "Barometric Pressure Rate",
    },
    "beaufort": {
        "device_class": "enum",
        "icon": "mdi:windsock",
        "name": "Beaufort Scale",
    },
    "cloudbase": {
        "device_class": "distance",
        "icon": "mdi:cloud-arrow-down",
        "name": "Cloud Base Height",
    },
    "cloudcover": {
        "icon": "mdi:weather-cloudy-alert",
        "name": "Cloud Cover",
    },
    "co": {
        "device_class": "carbon_monoxide",
        "icon": "mdi:molecule-co",
        "name": "Carbon Monoxide",
    },
    "co2": {
        "device_class": "carbon_dioxide",
        "icon": "mdi:molecule-co2",
        "name": "Carbon Dioxide",
    },
    "consBatteryVoltage": {
        "device_class": "voltage",
        "icon": "mdi:sine-wave",
        "name": "Console Battery Voltage",
    },
    "cooldeg": {
        "icon": "mdi:snowflake-thermometer",
        "name": "Cooling Degree Days",
    },
    "dateTime": {
        "enabled_by_default": False,
        "device_class": "timestamp",
        "icon": "mdi:clock",
        "name": "Date Time",
    },
    "dayET": {
        "enabled_by_default": False,
        "icon": "mdi:waves-arrow-up",
        "name": "Day Evapotranspiration",
    },
    "dayRain": {
        "device_class": "precipitation",
        "icon": "mdi:cup-water",
        "name": "Day Rainfall",
    },
    "daySunshineDur": {
        "device_class": "duration",
        "icon": "mdi:sun-clock",
        "name": "Day Sunshine Duration",
    },
    "dewpoint": {
        "device_class": "temperature",
        "icon": "mdi:water-thermometer",
        "name": "Dew Point Temperature",
    },
    "extraAlarm": {
        "enabled_by_default": False,
        "icon": "mdi:alarm-light",
        "name": "Extra Alarm",
    },
    "extraHumid": {
        "device_class": "humidity",
        "icon": "mdi:water-percent",
        "name": "Extra Humidity",
    },
    "extraTemp": {
        "device_class": "temperature",
        "icon": "mdi:thermometer",
        "name": "Extra Temperature",
    },
    "forecastIcon": {
        "icon": "mdi:image-frame",
        "name": "Forecast Icon",
    },
    "forecastRule": {
        "icon": "mdi:format-list-numbered",
        "name": "Forecast Rule",
    },
    "growdeg": {
        "icon": "mdi:sprout",
        "name": "Growing Degree Days",
    },
    "gustdir": {
        "icon": "mdi:compass-rose",
        "name": "Wind Gust Direction",
    },
    "hail": {
        "device_class": "precipitation",
        "icon": "mdi:weather-hail",
        "name": "Hailfall",
    },
    "hailRate": {"icon": "mdi:weather-hail", "name": "Hail Rate"},
    "heatdeg": {
        "icon": "mdi:sun-thermometer",
        "name": "Heating Degree Days",
    },
    "heatindex": {
        "device_class": "temperature",
        "icon": "mdi:sun-thermometer",
        "name": "Heat Index",
    },
    "heatingTemp": {
        "device_class": "temperature",
        "icon": "mdi:sun-thermometer",
        "name": "Heating Temperature",
    },
    "heatingVoltage": {
        "device_class": "voltage",
        "icon": "mdi:sine-wave",
        "name": "Heating Voltage",
    },
    "highOutTemp": {
        "device_class": "temperature",
        "icon": "mdi:thermometer-high",
        "name": "High Outdoor Temperature",
    },
    "hourRain": {
        "device_class": "precipitation",
        "icon": "mdi:cup-water",
        "name": "Hourly Rainfall",
    },
    "humidex": {"icon": "mdi:water-percent", "name": "Humidex"},
    "illuminance": {
        "device_class": "illuminance",
        "icon": "mdi:sun-wireless",
        "name": "Illuminance",
    },
    "insideAlarm": {
        "enabled_by_default": False,
        "icon": "mdi:alarm-light",
        "name": "Inside Alarm",
    },
    "inDewpoint": {
        "device_class": "temperature",
        "icon": "mdi:water-thermometer",
        "name": "Indoor Dew Point",
    },
    "inHumidity": {
        "device_class": "humidity",
        "icon": "mdi:water-percent",
        "name": "Indoor Humidity",
    },
    "inTemp": {
        "device_class": "temperature",
        "icon": "mdi:thermometer",
        "name": "Indoor Temperature",
    },
    "interval": {"icon": "mdi:repeat", "name": "Interval"},
    "leafTemp": {
        "device_class": "temperature",
        "icon": "mdi:leaf-maple",
        "name": "Leaf Temperature",
    },
    "leafWet": {
        "device_class": "moisture",
        "icon": "mdi:leaf-maple",
        "name": "Leaf Wetness",
    },
    "lightning_distance": {
        "device_class": "distance",
        "icon": "mdi:flash",
        "name": "Lightning Distance",
    },
    "lightning_disturber_count": {
        "icon": "mdi:flash",
        "name": "Lightning Disturber Count",
    },
    "lightning_noise_count": {
        "icon": "mdi:flash",
        "name": "Lightning Noise Count",
    },
    "lightning_strike_count": {
        "icon": "mdi:flash",
        "name": "Lightning Strike Count",
    },
    "lowOutTemp": {
        "device_class": "temperature",
        "icon": "mdi:thermometer-low",
        "name": "Low Outdoor Temperature",
    },
    "maxSolarRad": {
        "device_class": "irradiance",
        "icon": "mdi:sun-wireless",
        "name": "Maximum Solar Radiation",
    },
    "monthET": {
        "enabled_by_default": False,
        "icon": "mdi:waves-arrow-up",
        "name": "Month Evapotranspiration",
    },
    "monthRain": {
        "device_class": "precipitation",
        "icon": "mdi:cup-water",
        "name": "Monthly Rainfall",
    },
    "nh3": {
        "icon": "mdi:chemical-weapon",
        "name": "Ammonia Concentration",
    },
    "no2": {
        "device_class": "nitrogen_dioxide",
        "icon": "mdi:chemical-weapon",
        "name": "Nitrogen Dioxide Concentration",
    },
    "noise": {
        "device_class": "sound_pressure",
        "icon": "mdi:volume-vibrate",
        "name": "Noise Level",
    },
    "o3": {
        "device_class": "ozone",
        "icon": "mdi:chemical-weapon",
        "name": "Ozone Concentration",
    },
    "outHumidity": {
        "device_class": "humidity",
        "icon": "mdi:water-percent",
        "name": "Outdoor Humidity",
    },
    "outsideAlarm": {
        "enabled_by_default": False,
        "icon": "mdi:alarm-light",
        "name": "Outside Alarm",
    },
    "outTemp": {
        "device_class": "temperature",
        "icon": "mdi:thermometer",
        "name": "Outdoor Temperature",
    },
    "outWetbulb": {
        "device_class": "temperature",
        "icon": "mdi:thermometer-water",
        "name": "Outdoor Wetbulb Temperature",
    },
    "pb": {
        "icon": "mdi:chemical-weapon",
        "name": "Lead Concentration",
    },
    "pm10_0": {
        "device_class": "pm10",
        "icon": "mdi:air-filter",
        "name": "PM10 Concentration",
    },
    "pm1_0": {
        "device_class": "pm1",
        "icon": "mdi:air-filter",
        "name": "PM1.0 Concentration",
    },
    "pm2_5": {
        "device_class": "pm25",
        "icon": "mdi:air-filter",
        "name": "PM2.5 Concentration",
    },
    "pop": {
        "icon": "mdi:cloud-percent",
        "name": "Probability of Precipitation",
    },
    "pressure": {
        "device_class": "atmospheric_pressure",
        "icon": "mdi:gauge",
        "name": "Atmospheric Pressure",
    },
    "pressureRate": {
        "icon": "mdi:gauge",
        "name": "Pressure Rate",
    },
    "radiation": {
        "device_class": "irradiance",
        "icon": "mdi:radioactive",
        "name": "Solar Radiation",
    },
    "rain": {
        "device_class": "precipitation",
        "icon": "mdi:cup-water",
        "name": "Rainfall",
    },
    "rain24": {
        "device_class": "precipitation",
        "icon": "mdi:cup-water",
        "name": "24-Hour Rainfall",
    },
    "rainDur": {
        "device_class": "duration",
        "icon": "mdi:timer",
        "name": "Rain Duration",
    },
    "rainRate": {
        "device_class": "precipitation_intensity",
        "icon": "mdi:weather-pouring",
        "name": "Rain Rate",
    },
    "referenceVoltage": {
        "device_class": "voltage",
        "icon": "mdi:sine-wave",
        "name": "Reference Voltage",
    },
    "rms": {
        "device_class": "wind_speed",
        "icon": "mdi:windsock",
        "name": "Root Mean Square Wind Speed",
    },
    "rxCheckPercent": {
        "icon": "mdi:radio-tower",
        "name": "Receive Check Percentage",
    },
    "soilLeafAlarm": {
        "enabled_by_default": False,
        "icon": "mdi:alarm-light",
        "name": "Soil Leaf Alarm",
    },
    "snow": {
        "device_class": "precipitation",
        "icon": "mdi:weather-snowy-heavy",
        "name": "Snowfall",
    },
    "snowDepth": {
        "device_class": "distance",
        "icon": "mdi:snowflake",
        "name": "Snow Depth",
    },
    "snowMoisture": {
        "device_class": "moisture",
        "icon": "mdi:snowflake-melt",
        "name": "Snow Moisture Content",
    },
    "snowRate": {
        "device_class": "precipitation_intensity",
        "icon": "mdi:snowflake",
        "name": "Snow Rate",
    },
    "so2": {
        "device_class": "sulphur_dioxide",
        "icon": "mdi:chemical-weapon",
        "name": "Sulfur Dioxide Concentration",
    },
    "soilMoist": {
        "device_class": "moisture",
        "icon": "mdi:water-percent",
        "name": "Soil Moisture",
    },
    "soilTemp": {
        "device_class": "temperature",
        "icon": "mdi:thermometer",
        "name": "Soil Temperature",
    },
    "stormRain": {
        "device_class": "precipitation",
        "icon": "mdi:cup-water",
        "name": "Storm Rainfall",
    },
    "stormStart": {
        "device_class": "timestamp",
        "icon": "mdi:clock-start",
        "name": "Storm Start Time",
    },
    "sunrise": {
        "device_class": "timestamp",
        "icon": "mdi:weather-sunset-up",
        "name": "Sunrise",
    },
    "sunset": {
        "device_class": "timestamp",
        "icon": "mdi:weather-sunset-down",
        "name": "Sunset",
    },
    "sunshineDur": {
        "device_class": "duration",
        "icon": "mdi:sun-clock",
        "name": "Sunshine Duration",
    },
    "supplyVoltage": {
        "device_class": "voltage",
        "icon": "mdi:sine-wave",
        "name": "Supply Voltage",
    },
    "totalRain": {
        "device_class": "precipitation",
        "icon": "mdi:cup-water",
        "name": "Total Rainfall",
    },
    "usUnits": {
        "attributes": {"options": "{{ ['METRIC','METRICWX','US'] }}"},
        "device_class": "enum",
        "icon": "mdi:scale-balance",
        "name": "Units",
    },
    "vecavg": {
        "device_class": "wind_speed",
        "icon": "mdi:windsock",
        "name": "Vector Average Wind Speed",
    },
    "vecdir": {
        "icon": "mdi:compass-rose",
        "name": "Vector Direction",
    },
    "wind": {
        "device_class": "wind_speed",
        "icon": "mdi:windsock",
        "name": "Wind Speed",
    },
    "windDir": {
        "icon": "mdi:compass-rose",
        "name": "Wind Direction",
    },
    "windDir10": {
        "icon": "mdi:compass-rose",
        "name": "10-Minute Wind Direction",
    },
    "windGust": {
        "device_class": "wind_speed",
        "icon": "mdi:windsock",
        "name": "Wind Gust Speed",
    },
    "windGustDir": {
        "icon": "mdi:compass-rose",
        "name": "Wind Gust Direction",
    },
    "windSpeed": {
        "device_class": "wind_speed",
        "icon": "mdi:windsock",
        "name": "Wind Speed",
    },
    "windSpeed10": {
        "device_class": "wind_speed",
        "icon": "mdi:windsock",
        "name": "10-Minute Wind Speed",
    },
    "windchill": {
        "device_class": "temperature",
        "icon": "mdi:thermometer",
        "name": "Wind Chill Temperature",
    },
    "windgustvec": {
        "device_class": "wind_speed",
        "icon": "mdi:windsock",
        "name": "Wind Gust Vector Speed",
    },
    "windrun": {
        "device_class": "distance",
        "icon": "mdi:windsock",
        "name": "Wind Run Distance",
    },
    "windvec": {
        "device_class": "wind_speed",
        "icon": "mdi:windsock",
        "name": "Wind Vector Speed",
    },
    "yearET": {
        "enabled_by_default": False,
        "icon": "mdi:waves-arrow-up",
        "name": "Year Evapotranspiration",
    },
    "yearRain": {
        "device_class": "precipitation",
        "icon": "mdi:cup-water",
        "name": "Yearly Rainfall",
    },
}
