# plcnext-mqtt
Service that publishes PLCnext tags to MQTT topics.

## Notes
- As of this commit, the tool only attempts to connect to the broker. It will exit upon successful connection or connection failure.
- Client certificate authentication is not yet supported, though authorization is still required.
- Until authentication is supported, do not use this in a production system. It is possible for an attacker to sniff the username and password from your connection, then use it to publish their own malicious data.

## Usage

### Installation
You can find installation instructions below.

### Configuration
Settings are provided via the config.JSON file. The provided config.JSON file is a template listing all required arguments. Additional arguments will be ignored.

## Installation
PLCnext installation instructions will be provided in the near future.