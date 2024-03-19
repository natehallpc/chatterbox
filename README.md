# plcnext-mqtt
Service that publishes PLCnext tags to MQTT topics.

## Notes
- As of this commit, the tool only attempts to connect to the broker. It will exit upon connection to the broker or if the connection times out.

## Usage

### Installation
You can find installation instructions below.

### Configuration
- Settings are provided via the config.JSON file. The provided config.JSON file is a template listing all possible arguments.
- Arguments not listed in the template will be ignored.
- All arguments in the template are required except key_file_password. If the key file is password protected and key_file_password is not provided, you will be promted to enter it on the command line.


## Installation
PLCnext installation instructions will be provided in the near future.