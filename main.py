import paho.mqtt.client as mqtt
import json
import ssl
import time
import logging

####################################################
# Define helper functions & callbacks
####################################################

# Uses the provided client to publish PLCnext tags to their respectively mapped MQTT topics
def publish_tags(client: mqtt.Client, mappings: dict):
    if client.is_connected():
        logger.info(f'Publishing tags: \n{mappings}')

# CALLBACK: Connected to broker
def on_connect(client, userdata, flags, reason_code, properties):
    # reason_code takes the form of an MQTT-v5.0-specified name
    broker_url = client.host
    if client.is_connected():
        logger.info(f"Successfully connected to {broker_url}")
    else:
        logger.error(f"Broker connection unsuccessful. Reason code: {reason_code}")
        logger.info(f"Reattempting to connect to {broker_url}")
        client.connect(broker_url, 8883, 60)

# CALLBACK: Connection timeout
def on_connect_fail(client, userdata):
    broker_url = client.host
    logger.error("The broker did not respond in time. Waiting 60s to try again.")
    time.sleep(60)
    logger.info(f"Reattempting to connect to {broker_url}")
    client.connect(broker_url, 8883, 60)

# CALLBACK: Broker connection severed
def on_disconnect(client, userdata, disconnect_flags, reason_code, properties):
    broker_url = client.host
    logger.error(f"The connection to {broker_url} was broken. Attempting to reconnect.")
    client.connect(broker_url, 8883, 60)

# CALLBACK: Received update from broker on subscribed topic
def on_message(client, userdata, message):
    pass

# CALLBACK: Log information has become available
def on_log(client, userdata, level, buf):
    logger.info(buf)


####################################################
# Load settings 
####################################################
    
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
mappings = settings.get('tag_topic_mappings', None)
if not mappings:
    print("ERROR: tag_topic_mappings not found in configuration file.")  
    raise SystemExit
time_between_publications = settings.get('time_between_publications', 10)
if type(time_between_publications) is not int:
    print("ERROR: time_between_publications must be an integer.")  
    raise SystemExit
log_file_name = settings.get('log_file', '/var/log/plcnext-mqtt.log')
logger = logging.getLogger(__name__)
try:
    logging.basicConfig(filename=log_file_name, encoding='utf-8', level=logging.DEBUG)
except OSError:
    print("ERROR: invalid log file. Make sure the specified directory exists and that you have permission to write to it.")
    raise SystemExit


####################################################
# Connect to broker and start the indefinite loop
####################################################
    
# Initialize client and register its callbacks
mqtt_client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2, client_id=client_id)
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.on_log = on_log
mqtt_client.on_disconnect = on_disconnect
mqtt_client.on_connect_fail = on_connect_fail
mqtt_client.tls_set(ca_certs=ca_cert_file, certfile=cert_file, keyfile=key_file, keyfile_password=key_file_password, tls_version=ssl.PROTOCOL_TLSv1_2)
mqtt_client.username_pw_set(username=username, password=password)

# Attempt to connect with a timeout of 60 seconds
logger.info(f"Attempting to connect to {broker_url}")
mqtt_client.connect(broker_url, 8883, 60)

mqtt_client.loop_start()
while True:
    publish_tags(mqtt_client, mappings)
    time.sleep(time_between_publications)