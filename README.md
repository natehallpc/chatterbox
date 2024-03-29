# chatterbox
Python application interconnecting the PLCnext runtime environment with a remote MQTT broker.

## Usage

### Overview

When installed as directed, this script runs at startup and respawns if killed. It reads tag values from the PLCnext and publishes them to topics on an MQTT broker with configurable frequency.

Configuration instructions can be found below, and installation instructions are in their own section further down.

### Configuration
- Settings are provided via the `config.json` file. The provided file is a template listing all possible arguments.
- Arguments not listed in the template will be ignored.
- All arguments in the template are required except  those specified in the defaults section below. If the key file is password protected and `key_file_password` is not provided, you will be promted to enter it on the command line.

### Defaults
```
plc_address: 'localhost'
log_file`: '/var/log/chatterbox.log'
log_verbose: false
seconds_between_publications: 10
publish_qos: 0
retain_topics: false
key_file_password: None
```

## Installation

In addition to the usual installation instructions, such as installing libraries; a few steps need to be taken in order to register this application as a service. Doing so ensures it will run when your controller powers on.

Before following these instructions, **be sure your PLCnext controller has internet access**. This will be necessary in general if your MQTT broker is not on a local subnet, but is also needed for the installation process. There are guides online which can guide you through this process; I won't provide any as it depends on your network and hardware. Best of luck!

### Instructions

1. Connect to PLCnext as `admin` user via SSH.

2. Set a `root` user password:
    ```
    sudo passwd root
    ```

3. Allow `root` login via SSH:
    - Use Vim or Nano to open `/etc/ssh/sshd_config`
    - Uncomment or add the line `PermitRootLogin yes`
    - Save the file and exit
    - `sudo /etc/init.d/sshd restart`

4. As `root`, use a tool like SFTP or SCP to transfer files to the PLC. 

    Place `chatterboxd` in `/etc/init.d/`
    
    Place remaining files in `/opt/plcnext/chatterbox/`. You will need to create the `chatterbox` directory. Make sure `chatterbox.py` and `config.json` are in this exact directory, and not a subdirectory.
     

    Necessary files are:
    - `chatterbox.py`
    - Client cert file
    - Client key file
    - CA cert file
    - `config.json`

5. SSH into the controller as `root` or log in as another user and run `su`

6. Change `chatterbox.py`  and `chatterboxd` permissions to allow execution: 

    ```
    chmod +x /opt/plcnext/chatterbox/chatterbox.py
    chmod +x /etc/init.d/chatterboxd
    ```

7. Install `pip`:

    ```
    curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
    python3 get-pip.py
    ```

8. Install necessary libraries

    ```
    python3 -m pip install paho-mqtt
    python3 -m pip install PyPlcnextRsc
    ```

9. Register the new service

    ```
    cd /etc/init.d/
    update-rc.d chatterboxd defaults
    ```

10. Start the service!

    ```
    service chatterboxd start
    ```