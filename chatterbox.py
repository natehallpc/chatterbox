import paho.mqtt.client as mqtt
import json
import ssl
import time
import logging
import sys
from PyPlcnextRsc import Device, GUISupplierExample
from PyPlcnextRsc.Arp.Plc.Gds.Services import IDataAccessService


####################################################
# Define helper functions & callbacks
####################################################

# Uses the provided client to publish PLCnext tags to their respectively mapped MQTT topics
def publish_tags(data_service: IDataAccessService, client: mqtt.Client):
    mappings = client.user_data_get()['publish_mappings']
    if not client.is_connected() or mappings is None:
        return
    qos = client.user_data_get()['publish_qos']
    retain = client.user_data_get()['retain_topics']
    for tag in mappings:
        tag_prefix = client.user_data_get()['tag_prefix']
        full_tag = tag_prefix + tag
        tag_value = data_service.ReadSingle(full_tag).Value.GetValue()
        topic = mappings[tag]
        logger.debug(f"Publishing {full_tag}'s value of {tag_value} to topic {topic} with QOS {qos}")
        try:
            client.publish(topic=topic, payload=tag_value, qos=qos, retain=retain, properties=None)
        except:
            logger.error(f"Could not publish {tag}. Ensure that the topic ({topic}) is valid and the tag value ({tag_value}) is less than 268435455 bytes")

# Uses the provided client to initialize specified topic values with QOS 2.
def publish_initial_vals(client: mqtt.Client):
    mappings = client.user_data_get()['init_publishes']
    if mappings is None:
        return
    for topic in mappings:
        init_val = mappings[topic]
        logger.debug(f"Initializing {topic} with value {init_val}")
        try:
            client.publish(topic=topic, payload=init_val, qos=2)
        except:
            logger.error(f"Failed to initialize topic {topic}")

# Uses the provided client object to subscribe to topics needed to populate specified tags.
def subscribe_topics(client: mqtt.Client):
    mappings = client.user_data_get()['subscribe_mappings']
    if mappings is None:
        return
    tag_prefix = client.user_data_get()['tag_prefix']
    qos = client.user_data_get()['subscribe_qos']
    for topic in mappings:
        variable_name = tag_prefix + mappings[topic]
        try:
            logger.debug(f"Subscribing variable {variable_name} to topic {topic} with QOS {qos}")
            client.subscribe(topic=topic, qos=qos)
        except:
            logger.error(f"Failed to subscribe to {topic}. Ensure that it is a valid topic name.")

# CALLBACK: Connected to broker
def on_connect(client, userdata, flags, reason_code, properties):
    # reason_code takes the form of an MQTT-v5.0-specified name
    broker_url = client.host
    if client.is_connected():
        logger.info(f"Successfully connected to {broker_url}")
        # Subscribe and publish LWT-type messages from connect callback to ensure consistency across disconnection events
        publish_initial_vals(client=client)
        subscribe_topics(client=client)
    else:
        logger.error(f"Broker connection unsuccessful. Reason code: {reason_code}")

# CALLBACK: Connection timeout
def on_connect_fail(client, userdata):
    logger.error(f"Failed to connect to {broker_url}.")

# CALLBACK: Broker connection severed
def on_disconnect(client, userdata, disconnect_flags, reason_code, properties):
    broker_url = client.host
    logger.error(f"The connection to {broker_url} was broken. Will now attempt to reconnect until successful.")

# CALLBACK: Received update from broker on subscribed topic
def on_message(client, userdata, message):
    print(f"Subscribed topic {message.topic} was set to {message.payload.decode('utf-8')}")
    corresponding_tag = userdata['subscribe_mappings'].get(message.topic, None)
    if not corresponding_tag:
        logger.error(f"Received an update from topic {message.topic}, which has no corresponding PLCnext variable.")
        return
    

# CALLBACK: Log information has become available
def on_log(client, userdata, level, buf):
    logger.debug(buf)


####################################################
# Load settings 
####################################################
    
# Read JSON configuration file
try:
    config_file = open('/etc/chatterbox/config.json')
except:
    raise ValueError("config.json not found.")

settings = json.load(config_file)

# Parse config settings. Use walrus operator (:=) to assign variables
# while simultaneously performing error checks. Use None default for
# dictionary accesses rather than catching exceptions for missing values.
plc_address = settings.get('plc_address', 'localhost')
if not (broker_url := settings.get('broker_url', None)):
    raise ValueError("broker_url not found in configuration file.")
if not (cert_file := settings.get('cert_file', None)):
    raise ValueError("cert_file not found in configuration file.")
if not (key_file := settings.get('key_file', None)):
    raise ValueError("key_file not found in configuration file.")
key_file_password = settings.get('key_password', None)
if not (ca_cert_file := settings.get('ca_cert_file', None)):
    raise ValueError("ca_cert_file not found in configuration file.")
if not (client_id := settings.get('client_id', None)):
    raise ValueError("client_id not found in configuration file.")
if not (mqtt_username := settings.get('mqtt_username', None)):
    raise ValueError("mqtt_username not found in configuration file.")  
if not (mqtt_password := settings.get('mqtt_password', None)):
    raise ValueError("mqtt_password not found in configuration file.")
if not (plc_username := settings.get('plc_username', None)):
    raise ValueError("plc_username not found in configuration file.") 
if not (plc_password := settings.get('plc_password', None)):
    raise ValueError("plc_password not found in configuration file.")
if type(tag_prefix := settings.get('tag_prefix', 'Arp.Plc.Eclr/')) is not str:
    raise ValueError("tag_prefix must be a string.")
init_publishes = settings.get('initialize_topic_values', None)
if init_publishes is not None and type(init_publishes) is not dict:
    raise ValueError("initialize_topic_values is not a properly formatted dictionary.")
publish_mappings = settings.get('publish_tags_to_topics', None)
if publish_mappings is not None and type(publish_mappings) is not dict:
    raise ValueError("publish_tags_to_topics is not a properly formatted dictionary.")
subscribe_mappings = settings.get('subscribe_topics_to_tags', None)
if subscribe_mappings is not None and type(subscribe_mappings) is not dict:
    raise ValueError("subscribe_topics_to_tags is not a properly formatted dictionary.")
if type((time_between_publications := settings.get('seconds_between_publications', 10))) is not int:
    raise ValueError("time_between_publications must be an integer.")
log_file_name = settings.get('log_file', '/var/log/chatterbox.log')
log_verbose: bool = settings.get('log_verbose', False)
if (publish_qos := settings.get('publish_qos', 0)) not in [0, 1, 2]:
    raise ValueError("publish_qos must be an integer. Possible options are 0, 1, and 2.")
if (subscribe_qos := settings.get('subscribe_qos', 0)) not in [0, 1, 2]:
    raise ValueError("subscribe_qos must be an integer. Possible options are 0, 1, and 2.")
retain_topics = settings.get('retain_topics', False)

# Initialize logger
logger = logging.getLogger(__name__)
try:
    log_level = logging.DEBUG if log_verbose else logging.INFO
    format = '%(asctime)s - %(name)s - %(levelname)s: %(message)s'
    logging.basicConfig(filename=log_file_name, encoding='utf-8', level=log_level, format=format)
except:
    raise ValueError("invalid log file. Make sure the specified directory exists and that you have permission to write to it.")

# Configuration finished.
logging.info("chatterbox was started successfully.")


####################################################
# Connect to MQTT broker
####################################################
    
# Initialize client and register its callbacks
try:
    mqtt_client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2, client_id=client_id)
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    mqtt_client.on_log = on_log
    mqtt_client.on_disconnect = on_disconnect
    mqtt_client.on_connect_fail = on_connect_fail
    mqtt_client.tls_set(ca_certs=ca_cert_file, certfile=cert_file, keyfile=key_file, keyfile_password=key_file_password, tls_version=ssl.PROTOCOL_TLSv1_2)
    mqtt_client.username_pw_set(username=mqtt_username, password=mqtt_password)
    mqtt_client.user_data_set({ 
                               'tag_prefix': tag_prefix,
                               'init_publishes': init_publishes,
                               'publish_mappings': publish_mappings,
                               'subscribe_mappings': subscribe_mappings,
                               'publish_qos': publish_qos,
                               'subscribe_qos': subscribe_qos,
                               'retain_topics': retain_topics
                               })
except Exception as e:
    logging.error(e)

# Attempt to connect to the broker. Any immediate errors, such as connection refused or
# timed out, will be caught and logged. If the connection fails later, loop_start() 
# ensures the connection will be reattempted until successful. If the connection is lost
# later, it will be reestablished automatically.
try:
    logger.info(f"Attempting to connect to {broker_url}")
    mqtt_client.connect(host=broker_url, port=8883)
except Exception as e:
    logger.error(e)
    logger.info("Connection failed due to the above error. Waiting 60s to try again.")
mqtt_client.loop_start()


####################################################
# Connect to PLCnext RSC interface and communicate
# 'til the sun goes dark.
####################################################
secureInfoSupplier = lambda:(plc_username, plc_password)
while True:
    try:

        with Device(plc_address, secureInfoSupplier=secureInfoSupplier) as device:
            data_access_service = IDataAccessService(device)
            while True:
                publish_tags(data_service=data_access_service, client=mqtt_client)
                time.sleep(time_between_publications)
    except Exception as e:
        logger.error(e)
        time.sleep(20)
