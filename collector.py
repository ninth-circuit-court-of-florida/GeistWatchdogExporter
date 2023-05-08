#!/usr/bin/python3
from prometheus_client import start_http_server, Gauge
import xmltodict
import time
import urllib
import base64
import json
import logging
from logging.handlers import RotatingFileHandler

"""
Put your device addresses in the sources array
Put your auth credentials in the auth variables
the base64 for the base64 string for basic auth that the 1200 model requires
you can generate that string with an online converter or cli tools just search for "Basic Authentication Header Generator"
"""

sources_1200 = ['http://127.0.0.1/data.xml',
                'http://127.0.0.2/data.xml']
sources_100NPS = ['http://127.0.0.3/',
                  'http://127.0.0.4/']

auth_username = ''
auth_password = ''
base64string = ''

"""
Retrieves an authentication token from a URL using a provided password.

Args:
    url (str): The URL to retrieve the authentication token from.
    password (str): The password to use for authentication.

Returns:
    bytes: The data returned from the URL after authentication.
"""
def getAuthToken(url, password):
    post_data = {"token": "", "cmd": "login", "data": {"password": password}}
    json_post_data = json.dumps(post_data)
    encoded_post_data = json_post_data.encode('utf-8')
    request = urllib.request.Request(
        url, data=encoded_post_data, method='POST')
    openUrl = urllib.request.urlopen(request)
    if (openUrl.getcode() == 200):
        data = openUrl.read()
    else:
        print("Error receiving data", openUrl.getcode())
    return data

"""
Sets up logging for the application.

This function creates a RotatingFileHandler and a StreamHandler to allow the script to log messages
to a file and to the console.

:return: None
"""
def setup_logging():
    log_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s')
    log_file = "geist_collector.log"

    # Set up the RotatingFileHandler with a max size of 1MB and keep up to 3 backup files
    file_handler = RotatingFileHandler(
        log_file, maxBytes=1 * 1024 * 1024, backupCount=3)
    file_handler.setFormatter(log_formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)

    logging.basicConfig(level=logging.DEBUG, handlers=[
                        console_handler, file_handler])

"""
Sends an HTTP request to the given URL with the specified model and token
and returns the response data.

Args:
    url (str): The URL to send the request to.
    model (str): The model to use for the request (either "1200" or "100NPS").
    token (str, optional): The token to include in the request data when model is "100NPS".

Returns:
    bytes: The response data from the URL.
"""
def getResponse(url, model, token=None):
    request = urllib.request.Request(url)
    if model == "1200":
        request.add_header("Authorization", "Basic %s" % base64string)
    if model == "100NPS":
        post_data = {"token": token, "cmd": "get"}
        json_post_data = json.dumps(post_data)
        encoded_post_data = json_post_data.encode('utf-8')
        request = urllib.request.Request(
            url, data=encoded_post_data, method='POST')
    openUrl = urllib.request.urlopen(request)
    if (openUrl.getcode() == 200):
        data = openUrl.read()
    else:
        print("Error receiving data", openUrl.getcode())
    return data

def parseResponse(response, model):

    if model == "1200":
        response_dict = xmltodict.parse(response)
        data = response_dict["server"]["devices"]["device"]
    if model == "100NPS":
        response = json.loads(response)["data"]
        for id in response:
            data = response[id]
    return data

"""
Parses a device based on its model, and extracts sensor data from it.

:param device: A dictionary representing the device, with some fields and/or
                sensors.
:type device: dict
:param model: A string representing the model of the device.
:type model: str
:return: A list of floats representing the values of the sensors extracted
          from the device.
:rtype: list
"""
def parseDevice(device, model):
    sensors = []
    if model == "1200":
        for sensor in device['field']:
            if sensor["@key"] == "TempF":
                sensors.append(float(sensor["@value"]))
            if sensor["@key"] == "Humidity":
                sensors.append(float(sensor["@value"]))
            if sensor["@key"] == "IO1":
                sensors.append(float(100 - int(sensor["@value"])))
    if model == "100NPS":
        for id in device:
            sensor = device[id]
            if sensor['type'] == "temperature":
                sensors.append(float(sensor['value']))
            if sensor['type'] == "humidity":
                sensors.append(float(sensor['value']))
            logging.debug(
                f"Sensor ID: {id}, Sensor Type: {sensor['type']}, Sensor Value: {sensor['value']}")

    logging.debug(
        f"Location: {device.get('@name', 'unknown')}, Model: {model}, Sensors: {sensors}")
    return sensors

"""
Updates the values of three Prometheus gauges that correspond to temperature, humidity, and water sensors.
:param source: source of the data
:param model: model of the data
:param temp_g: Prometheus Gauge object for temperature readings
:param humidity_g: Prometheus Gauge object for humidity readings
:param water_sensor_g: Prometheus Gauge object for water sensor readings
:return: location of the last device found in the data
"""
def update_gauge_values_1200(source, model, temp_g, humidity_g, water_sensor_g):
    data = parseResponse(getResponse(source, model), model)
    for device in data:
        location = device["@name"]
        sensors = parseDevice(device, model)
        for i in range(len(sensors)):
            if i == 0:
                temp_g.labels(location).set(sensors[i])
            if i == 1:
                humidity_g.labels(location).set(sensors[i])
            if i == 2:
                water_sensor_g.labels(location).set(sensors[i])
    return location

"""
Updates gauge values of temperature and humidity for a given source and model.
:param source: The source of the data.
:param model: The model of the data.
:param temp_g: The temperature gauge.
:param humidity_g: The humidity gauge.
:param token: The token for authorization.
:return: The location of the data.
"""
def update_gauge_values_100NPS(source, model, temp_g, humidity_g, token):
    data_response = getResponse(source, model, token)
    data = parseResponse(data_response, model)
    location = data["label"]
    device = data["entity"]["0"]["measurement"]
    sensors = parseDevice(device, model)
    for i in range(len(sensors)):
        if i == 0:
            temp_g.labels(location).set(sensors[i])
        if i == 1:
            humidity_g.labels(location).set(sensors[i])
    return location

"""
Resets the gauge values for a given location.

Args:
    location (str): The location to reset the gauge values for.
    temp_g (Gauge): The temperature gauge.
    humidity_g (Gauge): The humidity gauge.
    water_sensor_g (Gauge, optional): The water sensor gauge. Defaults to None.
"""
def reset_gauge_values(location, temp_g, humidity_g, water_sensor_g=None):
    temp_g.labels(location).set(-1)
    humidity_g.labels(location).set(-1)
    if water_sensor_g:
        water_sensor_g.labels(location).set(-1)


if __name__ == '__main__':
    setup_logging()
    logging.basicConfig(filename='exporter.log', level=logging.DEBUG)
    start_http_server(7000)
    temp_g = Gauge('environment_temp_f', 'Temperature in F', ['location'])
    humidity_g = Gauge('environment_humidity',
                       'Relative humidity percentage', ['location'])
    water_sensor_g = Gauge('environment_water_sensor',
                           'Relative humidity percentage', ['location'])
    while True:
        for source in sources_1200:
            model = "1200"
            try:
                location = update_gauge_values_1200(
                    source, model, temp_g, humidity_g, water_sensor_g)
            except Exception as e:
                print(f"Could not get data for source {source} ({model}): {e}")
                reset_gauge_values(
                    location, temp_g, humidity_g, water_sensor_g)

        for source in sources_100NPS:
            try:
                logging.debug(f"Processing 100NPS source: {source}")
                auth_url = source + 'api/auth/' + auth_username
                auth_response = json.loads(
                    getAuthToken(auth_url, auth_password))
                token = auth_response["data"]["token"]
                data_url = source + 'api/dev/'
                model = "100NPS"
                data_response = getResponse(data_url, model, token)
                data = parseResponse(data_response, model)
                location = data["label"]
                device = data["entity"]["0"]["measurement"]
                sensors = parseDevice(device, model)
                for i in range(len(sensors)):
                    if i == 0:
                        temp_g.labels(location).set(sensors[i])
                    if i == 1:
                        humidity_g.labels(location).set(sensors[i])
            except Exception as e:
                logging.error(
                    f"Could not get data for 100NPS source {source}: {e}")
    time.sleep(10)
