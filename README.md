# weewx-home-assistant 🌦️➡️🏠 #

[![GitHub Build Status](https://github.com/felddy/weewx-home-assistant/workflows/build/badge.svg)](https://github.com/felddy/weewx-home-assistant/actions)
[![CodeQL](https://github.com/felddy/weewx-home-assistant/workflows/CodeQL/badge.svg)](https://github.com/felddy/weewx-home-assistant/actions/workflows/codeql-analysis.yml)
[![Coverage Status](https://coveralls.io/repos/github/felddy/weewx-home-assistant/badge.svg?branch=develop)](https://coveralls.io/github/felddy/weewx-home-assistant?branch=develop)
[![Known Vulnerabilities](https://snyk.io/test/github/felddy/weewx-home-assistant/develop/badge.svg)](https://snyk.io/test/github/felddy/weewx-home-assistant)

This is a [WeeWX](http://www.weewx.com/) extension that publishes weather data
and configurations to [Home Assistant](https://www.home-assistant.io/) using the
[MQTT](https://mqtt.org/) protocol.

This extension is designed to be secure by default. By default encryption is
enabled.  Anonymous connections are not supported.

## Installation ##

```shell
pip install https://github.com/felddy/weewx-home-assistant/archive/refs/tags/v1.0.0.zip
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
    filter_keys = <default: dateTime,>
    node_id = <required>
    state_topic_prefix = <default: weather>
    unit_system = <default: METRICWX>
    [[mqtt]]
        client_id = <optional>
        hostname = <required>
        keep_alive = <default: 60>
        password = <required>
        port = <default: 8883>
        username = <required>
        use_tls = <default: True>
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
This project is in the public domain within the United States, and
copyright and related rights in the work worldwide are waived through
the [CC0 1.0 Universal public domain
dedication](https://creativecommons.org/publicdomain/zero/1.0/).

All contributions to this project will be released under the CC0
dedication. By submitting a pull request, you are agreeing to comply
with this waiver of copyright interest.
