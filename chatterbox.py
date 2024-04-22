import paho.mqtt.client as mqtt
import json
import ssl
import time
import logging
import logging.handlers
from PyPlcnextRsc import Device, RscVariant, RscType, IecType
from PyPlcnextRsc.Arp.Plc.Gds.Services import IDataAccessService, WriteItem, ReadItem, DataAccessError


####################################################
# Define helper functions
####################################################

# Returns the current date and time in an abbreviated, log-friendly format.
def time_str():
    return time.strftime("%Y-%m-%d %H:%M", time.localtime())

# Uses the provided client to publish PLCnext tags to their respectively mapped MQTT topics
def publish_tags(data_service: IDataAccessService, client: mqtt.Client):
    # Ensure that client is connected and holds necessary settings before proceeding.
    if (not client.is_connected()) or ((userdata := client.user_data_get()) is None):
        return
    # Make sure that publishing has actually been requested
    if (mappings := userdata['publish_mappings']) is None:
        return
    qos = userdata['publish_qos']
    retain = userdata['retain_topics']
    tag_prefix = userdata['tag_prefix']
    try:
        var_names = list(mappings.keys())
        var_names_full = [tag_prefix + var for var in var_names]
        read_items = data_access_service.Read(var_names_full)
    except Exception:
        logger.error("There was an error reading variables from the controller.")
    read_index = 0
    for var in var_names:
        topic = mappings[var]
        tag_item = read_items[read_index]
        if tag_item.Error != DataAccessError.NONE:
            logger.error(f"Unable to read the value of {var} from the controller. Error code: {tag_item.Error}")
            read_index += 1
            continue
        tag_value = tag_item.Value.GetValue()
        logger.debug(f"{time_str()} - Publishing {var}'s value of {tag_value} to topic {topic} with QOS {qos}")
        try:
            client.publish(topic=topic, payload=tag_value, qos=qos, retain=retain, properties=None)
        except:
            logger.error(f"{time_str()} - Could not publish {var}. Ensure that the topic ({topic}) is valid and the tag value ({tag_value}) is less than 268435455 bytes")
        read_index += 1

# Uses the provided client to initialize specified topic values with QOS 2.
def publish_initial_vals(client: mqtt.Client):
    # Ensure that client is connected and holds necessary settings before proceeding.
    if ((userdata := client.user_data_get()) is None) or ((mappings := userdata['init_publishes']) is None):
        return
    for topic in mappings:
        init_val = mappings[topic]
        logger.debug(f"{time_str()} - Initializing {topic} with value {init_val}")
        try:
            client.publish(topic=topic, payload=init_val, qos=2)
        except:
            logger.error(f"{time_str()} - Failed to initialize topic {topic}")

# Used for subscribe_mappings. Validates iec_type of each PLCnext variable, and
# replaces its string value with the corresponding RSC type. Returns an 
# updated dictionary with misconfigured subscriptions removed.
def fill_rsc_types(subscriptions: dict):
    # Don't try to iterate over an empty set of keys
    if not subscriptions:
        return
    iec_types = {
                'NULL': IecType.Null,
                'TIME': IecType.TIME,
                'LTIME': IecType.LTIME,
                'LDATE': IecType.LDATE,
                'LDATE_AND_TIME': IecType.LDATE_AND_TIME,
                'LTIME_OF_DAY': IecType.LTIME_OF_DAY,
                'BOOL': IecType.BOOL,
                'STRING': IecType.STRING,
                'LREAL': IecType.LREAL,
                'REAL': IecType.REAL,
                'LWORD': IecType.LWORD,
                'DWORD': IecType.DWORD,
                'WORD': IecType.WORD,
                'BYTE': IecType.BYTE,
                'LINT': IecType.LINT,
                'DINT': IecType.DINT,
                'INT': IecType.INT,
                'SINT': IecType.SINT,
                'ULINT': IecType.ULINT,
                'UDINT': IecType.UDINT,
                'UINT': IecType.UINT,
                'USINT': IecType.USINT
            }
    updated_dict = dict()
    for topic in subscriptions:
        try:
            subscription = subscriptions[topic]
            datatype = subscription['iec_type'].upper()
            iec_type = iec_types[datatype]
            subscription.update({'iec_type': iec_type})
            updated_dict.update({topic: subscription})
        except:
             logger.error(f"{time_str()} - Invalid subscription settings to topic {topic}. The subscription will not be made.")
    return updated_dict

# Uses the provided client object to subscribe to topics needed to populate specified tags.
def subscribe_topics(client: mqtt.Client):
    if (userdata := client.user_data_get()) is None:
        logger.error(f"{time_str()} - Couldn't make subscriptions due to an unknown error.")
        return
    if (subscriptions := userdata['subscribe_mappings']) is None:
        logger.info(f"{time_str()} - No subscriptions requested.")
        return
    tag_prefix = client.user_data_get()['tag_prefix']
    qos = client.user_data_get()['subscribe_qos']
    for topic in subscriptions:
        subscription = subscriptions[topic]
        variable_name = tag_prefix + subscription['plcnext_tag_path']
        try:
            logger.debug(f"{time_str()} - Subscribing variable {variable_name} to topic {topic} with QOS {qos}")
            client.subscribe(topic=topic, qos=qos)
        except:
            logger.error(f"{time_str()} - Failed to subscribe to {topic}. Ensure that it is a valid topic name.")

# Take in an MQTT payload (a byte string) and cast it to a Python variable
# based on its IEC type, packaging into an RscVariant.
def cast_bytes(bytestr: bytes, iec_type: IecType) -> RscVariant:
    payload = bytestr.decode('utf-8')
    try:
        match iec_type:
            case IecType.Null:
                return RscVariant(value=bytestr, rscType=iec_type)
            case IecType.TIME | IecType.LTIME:
                return RscVariant(value=payload, rscType=iec_type)
            case IecType.LDATE | IecType.LDATE_AND_TIME | IecType.LTIME_OF_DAY:
                return RscVariant(value=int(payload), rscType=iec_type)
            case IecType.BOOL:
                return RscVariant(value=(payload == 'True'), rscType=iec_type)
            case IecType.STRING:
                return RscVariant(value=payload, rscType=RscType.Utf8String)
            case IecType.REAL | IecType.LREAL:
                return RscVariant(value=float(payload), rscType=iec_type)
            case IecType.BYTE | IecType.WORD | IecType.DWORD | IecType.LWORD:
                return RscVariant(value=bytestr, rscType=iec_type)
            case IecType.SINT | IecType.INT | IecType.DINT | IecType.LINT:
                return RscVariant(value=int(payload), rscType=iec_type)
            case IecType.USINT | IecType.UINT | IecType.UDINT | IecType.ULINT:
                return RscVariant(value=int(payload), rscType=iec_type)
            case _ :
                logger.error(f"{time_str()} - Cast failed due to invalid IEC type. Provided type: {iec_type}")
                return RscVariant(value=None, rscType=iec_type)
    except:
        logger.error(f"{time_str()} - Failed to cast payload {bytestr} to an RscVariant.")
        return RscVariant(value=None, rscType=IecType.Null)


####################################################
# Define Paho MQTT client callbacks
####################################################

# CALLBACK: Connected to broker
def on_connect(client, userdata, flags, reason_code, properties):
    # reason_code takes the form of an MQTT-v5.0-specified name
    broker_url = client.host
    if client.is_connected():
        logger.info(f"{time_str()} - Successfully connected to {broker_url}")
        # Subscribe and publish LWT-type messages from connect callback to ensure consistency across disconnection events
        publish_initial_vals(client=client)
        subscribe_topics(client=client)
    else:
        logger.error(f"{time_str()} - Broker connection unsuccessful. Reason code: {reason_code}")

# CALLBACK: Connection timeout
def on_connect_fail(client, userdata):
    logger.error(f"{time_str()} - Failed to connect to {broker_url}.")

# CALLBACK: Broker connection severed
def on_disconnect(client, userdata, disconnect_flags, reason_code, properties):
    broker_url = client.host
    logger.error(f"{time_str()} - The connection to {broker_url} was broken with reason code {reason_code}. Will now attempt to reconnect until successful.")

# CALLBACK: Received update from broker on subscribed topic
def on_message(client, userdata, message):
    topic = message.topic
    subscription_settings = userdata['subscribe_mappings'][topic]
    iec_type = subscription_settings['iec_type']
    new_val = cast_bytes(message.payload, iec_type)
    logger.debug(f"{time_str()} - Subscribed topic {topic} was set to {new_val.GetValue()}")
    corresponding_tag = subscription_settings.get('plcnext_tag_path', "")
    if not corresponding_tag:
        logger.error(f"{time_str()} - Received an update from topic {message.topic}, which has no corresponding PLCnext variable.")
        return
    tag_prefix = client.user_data_get()['tag_prefix']
    var_name = tag_prefix + corresponding_tag
    try:
        data_access_service.WriteSingle(WriteItem(var_name, new_val))
        logger.debug(f"{time_str()} - Set variable {var_name} to {new_val}")
    except Exception as e:
        logger.error(f"{time_str()} - {e}")

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

# Validate and process subscription settings
subscribe_mappings = fill_rsc_types(subscribe_mappings)

# Initialize logger
logger = logging.getLogger(__name__)
try:
    logger.setLevel(logging.DEBUG if log_verbose else logging.INFO)
    # Limit log file size to 1MB, rotate 5 backups.
    log_size_handler = logging.handlers.RotatingFileHandler(log_file_name, maxBytes=1000000, backupCount=5)
    logger.addHandler(log_size_handler)
except:
    raise ValueError("invalid log file. Make sure the specified directory exists and that you have permission to write to it.")

# Configuration finished.
logger.info(f"{time_str()} - chatterbox was started successfully.")


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
    logger.error(f"{time_str()} - {e}")

# Attempt to connect to the broker. Any immediate errors, such as connection refused or
# timed out, will be caught and logged. If the connection fails later, loop_start() 
# ensures the connection will be reattempted until successful. If the connection is lost
# later, it will be reestablished automatically.
try:
    logger.info(f"{time_str()} - Attempting to connect to {broker_url}")
    mqtt_client.connect(host=broker_url, port=8883)
except Exception as e:
    logger.error(f"{time_str()} - {e}")
    logger.info(f"{time_str()} - Connection failed due to the above error. Waiting 60s to try again.")
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
                if publish_mappings:
                    publish_tags(data_service=data_access_service, client=mqtt_client)
                time.sleep(time_between_publications)
    except Exception as e:
        logger.error(f"{time_str()} - {e}")
        time.sleep(20)
