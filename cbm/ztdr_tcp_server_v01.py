import socket
import threading
import time
from base_socket.tcp_socket import ThreadedTcpServer, ThreadedTcpRequestHandler
from cbm_sensor_devices.ztdr_daq import ZtdrController
import numpy as np
import pandas as pd
import os

DAQ_0_IP = '192.168.0.200'
DAQ_0_PORT = 1025

DAQ_1_IP = '192.168.0.201'
DAQ_1_PORT = 1025

ZTDR_IP = 'localhost'
ZTDR_PORT = 60000

VIRTUAL_DAQ_ROOT_PATH = 'cbm_sensor_devices/daq_training_data'

class MyTcpHandler(ThreadedTcpRequestHandler):
    count = 0

    def data_received_task(self, data):
        if data['cmd'] == 'once':
            self.data_sending_task()
        elif data['cmd'] == 'start':
            time_interval = data['interval']
            self.start_send_timer(time_interval)
        elif data['cmd'] == 'stop':
            self.stop_send_timer()
        elif data['cmd'] == 'set_params':
            if 'params' in data.keys():
                params = data['params']
                ztdr_controller = self.server.get_controller_handle()
                ztdr_controller.set_tdr_control_parameters(params)

    def data_sending_task(self):
        pass

    def periodic_data_sending_task(self):
        # get controller handle to access server's working data
        ztdr_controller = self.server.get_controller_handle()
        # set data
        message = {}
        ztdr_data = ztdr_controller.get_recent_data()

        if ztdr_data is not None:
            key = ztdr_controller.get_device_name()
            message[key] = ztdr_data
        if len(message) > 0:
            self.send_data_to(self.request, message)

host_ip = socket.gethostbyname(socket.gethostname())
port = 10001


ztdr_controller = ZtdrController('ztdr', ZTDR_IP, ZTDR_PORT)
server = ThreadedTcpServer((host_ip, port), MyTcpHandler, ztdr_controller)

server.start()

ztdr_controller.start_send_timer(1.0)
ztdr_controller.start_receive_thread()

print("="*60)
print(f'ZTDR PROXY TCP Server (ip:{host_ip}, port:{port}) is running')
print('Device names = [ztdr]')
print("-"*60)
while True:
    time.sleep(1)
