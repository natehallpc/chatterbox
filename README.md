# chatterbox
Service that periodically publishes PLCnext tags to MQTT topics.

## Usage

### Overview

When installed as directed, this script runs at startup and respawns if killed. It reads tag values from the PLCnext REST API and publishes them to topics on an MQTT broker with configurable frequency.

Configuration instructions can be found below, and installation instructions are in their own section further down.

### Configuration
- Settings are provided via the `config.JSON` file. The provided file is a template listing all possible arguments.
- Arguments not listed in the template will be ignored.
- All arguments in the template are required except `key_file_password` and those specified in the defaults section below. If the key file is password protected and `key_file_password` is not provided, you will be promted to enter it on the command line.

### Defaults
- `log_file`: `/var/log/chatterbox.log`
- `seconds_between_publications`: `10`
- `publish_qos`: `0`
- `retain_topics`: `false`

## Installation

NOTE: Installation steps below are incomplete and should not be used yet.

Several steps must be taken to ensure that this program is ran at startup and respawned after any unexpected failure.

1. Connect to PLCnext as `admin` user via SSH.

2. Set a `root` user password:
    - `sudo passwd root`
    - Enter `admin`'s password
    - Enter `root`'s new password, then reenter to confirm.

3. Allow `root` login via SSH:
    - Use Vim or Nano to open `/etc/ssh/sshd_config`
    - Uncomment or add the line `PermitRootLogin yes`.
    - Save the file and exit
    - `sudo /etc/init.d/sshd restart`

4. As `root`, use a tool like SFTP or SCP to transfer files to the PLC. 
    
    Place them in `/opt/plcnext/chatterbox`. You will need to create the `chatterbox` directory.
     

    Necessary files are:
    - `main.py`
    - Client cert file
    - Client key file
    - CA cert file
    - `config.JSON`

5. SSH into the controller as `root`.

6. Change `main.py` permissions to allow execution: 

    `chmod +x /opt/plcnext/chatterbox/main.py`

...



    ```
    python3 -m pip install paho-mqtt
    python3 -m pip install pyPLCn
    ```