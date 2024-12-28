# weewx-home-assistant 🌦️➡️🏠 #

[![GitHub Build Status](https://github.com/felddy/weewx-home-assistant/workflows/build/badge.svg)](https://github.com/felddy/weewx-home-assistant/actions)
[![CodeQL](https://github.com/felddy/weewx-home-assistant/workflows/CodeQL/badge.svg)](https://github.com/felddy/weewx-home-assistant/actions/workflows/codeql-analysis.yml)
[![Coverage Status](https://coveralls.io/repos/github/felddy/weewx-home-assistant/badge.svg?branch=develop)](https://coveralls.io/github/felddy/weewx-home-assistant?branch=develop)
[![Known Vulnerabilities](https://snyk.io/test/github/felddy/weewx-home-assistant/develop/badge.svg)](https://snyk.io/test/github/felddy/weewx-home-assistant)

This [WeeWX](http://www.weewx.com/) extension simplifies the integration of a
weather station with [Home Assistant](https://www.home-assistant.io/). By
leveraging Home Assistant's [MQTT](https://mqtt.org/) discovery protocol, it
automatically creates entities for weather data, significantly reducing manual
configuration. Additionally, it ensures that all weather data is securely
transmitted and devices are always accurately represented, thanks to its support
for availability messages.

Key Features:

- **Simplified Setup**: Implements Home Assistant's MQTT discovery, allowing
  easy and automatic integration of weather station measurements.
- **Secure by Default**: Encryption is enabled, and anonymous connections are
  not supported, ensuring your data remains protected.
- **Robust Availability**: Supports MQTT Last Will and Testament (LWT) to
  accurately report device availability in Home Assistant.
- **Flexible Integration**: Supports multiple sensors and measurements with
  dynamic configuration, adapting easily to different weather station models and
  measurement units.

## Prerequisites ##

- A functioning installation of [WeeWX](http://www.weewx.com/) version `5.1` or
later using [Python](https://www.python.org/) version `3.10` or later.
- A functioning MQTT broker.

> [!TIP]
> We recommend using our [WeeWX Docker
> image](https://github.com/felddy/weewx-docker) to simplify the installation
> and configuration of WeeWX in conjunction with the
> [Mosquitto](https://mosquitto.org/) broker which can be installed as a [Home
> Assistant
> add-on](https://github.com/home-assistant/addons/blob/master/mosquitto/DOCS.md).

## Installation ##

```shell
pip install git+https://github.com/felddy/weewx-home-assistant@v1.0.0
```

## Configuration ##

Add the extension controller to `report_services` in the `weewx.conf` file:

```ini
[Engine]
    [[Services]]
        report_services = weewx_ha.Controller
```

Add a configuration section to the root of the `weewx.conf` file:

```ini
[HomeAssistant]
    node_id = weewx
    [[mqtt]]
        hostname = mqtt.example.com
        password = mqttPassword
        username = mqttUser
    [[station]]
        name = Weather Station
        model = Vantage Vue
        manufacturer = Davis
```

> [!IMPORTANT]
>
> - The `node_id` is used to group the weather station entities in the [MQTT
>   discovery
>   topic](https://www.home-assistant.io/integrations/mqtt/#discovery-messages).
> - The `station.name` is used by Home Assistant as the device name and the
>   prefix to all entities.

## Advanced Configuration ##

```ini
[HomeAssistant]
    discovery_topic_prefix = <default: homeassistant>
    node_id = <required>
    state_topic_prefix = <default: weather>
    unit_system = <default: METRICWX>
    [[mqtt]]
        client_id = <optional>
        hostname = <required>
        keep_alive = <optional: 60>
        password = <required>
        port = <optional: 8883>
        username = <required>
        use_tls = <optional: True>
        [[[tls]]]
            cadata = <optional>
            cafile = <optional>
            capath = <optional>
            certfile = <optional>
            keyfile = <optional>
            password = <optional>
    [[station]]
        manufacturer = <required>
        model = <required>
        name = <required>
        timezone = <default: UTC>
```

> [!NOTE]
> Information about `TLS` options can be found in the Python documentation:
>
> - `cadata`, `cafile`, `capath`:
>   [ssl.create_default_context](https://docs.python.org/3/library/ssl.html#ssl.create_default_context)
> - `certfile`, `keyfile`, `password`:
>   [ssl.SSLContext.load_cert_chain](https://docs.python.org/3/library/ssl.html#ssl.SSLContext.load_cert_chain)

## Contributing ##

We welcome contributions!  Please see [`CONTRIBUTING.md`](CONTRIBUTING.md) for
details.

## License ##

This project is released as open source under the [MIT license](LICENSE).

All contributions to this project will be released under the same MIT license.
By submitting a pull request, you are agreeing to comply with this waiver of
copyright interest.
