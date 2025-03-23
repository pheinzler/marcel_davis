from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import yaml
import os
from datetime import datetime

class Stats:
    def __init__(self, persist):
        self._persist = persist
        if persist:
            with open('./../conf/config.yaml', 'r') as file:
                conf = yaml.safe_load(file)
            self._org = conf["influx"]["org"]
            self._bucket= conf["influx"]["bucket"]
            self._token = os.getenv("INFLUX_TOKEN")
            self._url = os.getenv("INFLUX_URL")
            self._client = InfluxDBClient(url=self._url, token=self._token, org=self._org)
            self._write_api = self._client.write_api(write_options=SYNCHRONOUS)

    def send_handler(self, handler:str):
        if not self._persist:
            return
        date = datetime.now()
        date = date.strftime('%Y-%m-%d')
        point = Point("calls") \
        .tag("handler", handler) \
        .field("amount", 1.0 ) \
        .time(date)
        self._write_api.write(bucket=self._bucket, org=self._org, record=point)
        return
    
    def send_menue(self, today:dict):
        if today["status"] != 200:
            return
        date = datetime.now()
        date = date.strftime('%Y-%m-%d')
        for menue in today["day"]:
            if menue == "No Menu":
                break
            point = Point("meals") \
            .tag("category", menue) \
            .field("name", today["day"][menue]) \
            .field("price", menue["price"]) \
            .time(date)
            self._write_api.write(bucket=self._bucket, org=self._org, record=point)
        return
