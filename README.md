# plcnext-mqtt
Service that publishes PLCnext tags to MQTT topics.

## Notes
- As of this commit, the tool attempts to connect to the broker but does not publish or subscribe to any topics. Once a connection is successfully established, it will simply log tag-topic mappings at the specified publish frequency.

## Usage

### Installation
You can find installation instructions below.

### Configuration
- Settings are provided via the config.JSON file. The provided config.JSON file is a template listing all possible arguments.
- Arguments not listed in the template will be ignored.
- All arguments in the template are required except key_file_password and seconds_between_publications. If the key file is password protected and key_file_password is not provided, you will be promted to enter it on the command line. If seconds_between_publications is not provided, tags will be published every 10 seconds.


## Installation

NOTE: Installation steps below are incomplete and should not be used yet.

Several steps must be taken to ensure that this program is ran at startup and restarted after any unexpected failure.

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
    
    Place them in `/opt/plcnext/plcnext-mqtt`. You will need to create the `plcnext-mqtt` directory and you can call it whatever you'd like.
     

    Necessary files are:
    - `main.py`
    - Client cert file
    - Client key file
    - CA cert file
    - `config.JSON`

5. SSH into the controller as `root`.

6. Change `main.py` permissions to allow execution: 

    `chmod +x /opt/plcnext/plcnext-mqtt/main.py`

7. 