"""
#Python module for inference by dnn model
#Main functions:
#    1. Load model
#    2. Inference by loaded model
#    3. Data collection from CBM DAQ server
#    4. Providing inference result to another client
#Developer: Heon-Hui Kim (2022. 04. 22)
"""
import sys
import pathlib

import matplotlib.pyplot as plt
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import socket
import numpy as np
import pickle
from base_socket.tcp_socket import TcpClient, ThreadedTcpRequestHandler, ThreadedTcpServer
import queue
import time
from matplotlib.animation import FuncAnimation

class TdrBasedLeakDetection(TcpClient):

    def __init__(self, device_name, daq_ip, daq_port, daq_request_interval, model_file):
        super().__init__(daq_ip, daq_port)
        self.daq_request_interval = daq_request_interval
        self.__data_list = []
        self.__max_data_list_size = 10
        self.__device_name = device_name
        self.__inference_model = None
        self.__is_inference_ready = False


        if self.__load_model(model_file):
            self.__is_inference_ready = True

    def request_periodic_data_sending(self, interval):
        data = {"cmd": 'start', 'interval': interval}
        self.send_data_to_server(data)
        print(f'[client] sending to server: {data}')

    # overriding method for TcpClient
    def data_sending_task(self):
        pass

    # overriding method for TcpClient
    def data_received_task(self, data):
        if data:
            if type(data) is dict:
                if 'ztdr' in data.keys():
                    self.put_data(data['ztdr'])

    def start(self):
        self.connect()
        self.start_received_thread()
        self.request_periodic_data_sending(self.daq_request_interval)

    def stop(self):
        self.disconnect()

    def get_device_name(self):
        return self.__device_name

    def put_data(self, data):
        if len(self.__data_list) >= self.__max_data_list_size:
            _ = self.__data_list.pop(0)
        self.__data_list.append(data)

    def get_data(self):
        return self.__data_list

    def __load_model(self, model_file):
        try:
            #self.__inference_model = keras.models.load_model(model_file)
            pass
            if self.__inference_model is not None:
                return True
        except IOError as e:
            print("Cannot load model. Check file path and name!!")
        finally:
            return False


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

    def data_sending_task(self):
        pass

    def periodic_data_sending_task(self):
        # get controller handle to access server's working data
        controller_handle = self.server.get_controller_handle()
        # carry out inference
        data = controller_handle.get_infer_colgging_message()
        if len(data) > 0:
            self.send_data_to(self.request, data)

# some environment variables: DAQ server ip & port
tdr_server_ip = '192.168.0.59'
tdr_server_port = 10001

# some environment variables: Inference server ip & port
inference_server_ip = socket.gethostbyname(socket.gethostname())
inference_server_port = 10005

# inference server is composed of a daq client and inference server
import os
print(os.getcwd())
model_file = ''

tdr_request_interval = 1.0
inference = TdrBasedLeakDetection('leak_detection', tdr_server_ip, tdr_server_port, tdr_request_interval, model_file)
server = ThreadedTcpServer((inference_server_ip, inference_server_port), MyTcpHandler, inference)
server.start()
inference.start()

print("="*60)
print(f'TDR-Based Pipe Leak Detection Inference Server (ip:{inference_server_ip}, port:{inference_server_port}) is running')
print('Device names = [leak_detection]')
print("-"*60)



while True:
    data = inference.get_data()
    if len(data) > 0:
        print(data[-1])
    time.sleep(1)

'''
# Example for implementing client class
class TestInferenceClient(TcpClient):
    def request_periodic_data_sending(self, interval):
        data = {"cmd": 'start', 'interval': interval}
        self.send_data_to_server(data)

    def data_sending_task(self):
        pass

    def data_received_task(self, data):
        if data:
            if type(data) is dict:
                if 'infer_clogging' in data.keys():
                    print(f'current clogging label: {data["infer_clogging"]}')
                    
inference_client = TestInferenceClient(socket.gethostbyname(socket.gethostname()), inference_server_port)
inference_client.connect()
inference_client.start_received_thread()
inference_client.request_periodic_data_sending(1.0)
'''
