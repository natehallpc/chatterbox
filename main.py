import paho.mqtt.client as mqtt
import json
import ssl

is_connected = False

# Define callback functions

# Connected to broker
def on_connect(client, userdata, flags, reason_code, properties):
    is_connected = reason_code == 'Success'
    if is_connected:
        print("Successfully connected to broker.")
    else:
        print(f"Broker connection unsuccessful. Reason code: {reason_code}")
    #raise SystemExit

# Connection timeout
def on_connect_fail(client, userdata):
    print("Failed to connect to broker.")
    raise SystemExit

# Received update from broker on subscribed topic
def on_message(client, userdata, message):
    pass

# Log information has become available
def on_log(client, userdata, level, buf):
    print("log: ", buf)

# Read JSON configuration file
try:
    config_file = open('config.JSON')
except OSError:
    print("ERROR: config.JSON not found.")
    raise SystemExit

settings = json.load(config_file)


# Parse config settings

broker_url = settings.get('broker_url', None)
if not broker_url:
    print("ERROR: broker_url not found in configuration file.")
    raise SystemExit

cert_file = settings.get('cert_file', None)
if not cert_file:
    print("ERROR: cert_file not found in configuration file.")
    raise SystemExit

key_file = settings.get('key_file', None)
if not key_file:
    print("ERROR: key_file not found in configuration file.")
    raise SystemExit

key_file_password = settings.get('key_password', None)

ca_cert_file = settings.get('ca_cert_file', None)
if not ca_cert_file:
    print("ERROR: ca_cert_file not found in configuration file.")
    raise SystemExit

client_id = settings.get('client_id', None)
if not client_id:
    print("ERROR: client_id not found in configuration file.")  
    raise SystemExit

username = settings.get('login_username', None)
if not username:
    print("ERROR: login_username not found in configuration file.")  
    raise SystemExit

password = settings.get('login_password', None)
if not password:
    print("ERROR: login_password not found in configuration file.")  
    raise SystemExit


# Connect to broker
    
# Initialize client and register its callbacks
mqtt_client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2, client_id=client_id)
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.on_log = on_log
mqtt_client.on_connect_fail = on_connect_fail
mqtt_client.tls_set(ca_certs=ca_cert_file, certfile=cert_file, keyfile=key_file, keyfile_password=key_file_password, tls_version=ssl.PROTOCOL_TLSv1_2)
mqtt_client.username_pw_set(username=username, password=password)

# Attempt to connect for a maximum of 60 seconds
mqtt_client.connect(broker_url, 8883, 60)

mqtt_client.loop_forever()