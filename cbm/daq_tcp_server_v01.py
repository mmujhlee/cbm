import socket
import threading
import time
from base_socket.tcp_socket import ThreadedTcpServer, ThreadedTcpRequestHandler
import cv2
import queue
from cbm_sensor_devices.rgb_camera import RgbCameraController
from cbm_sensor_devices.adam_daq import AdamDaqController
from cbm_sensor_devices.ztdr_daq import ZtdrController
from cbm_sensor_devices.virtual_daq import VirtualDaqController
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

    def data_sending_task(self):
        controller_handle = self.server.get_controller_handle()
        # set data
        data = controller_handle.get_controller_message()
        if len(data) > 0:
            self.send_data_to(self.request, data)

    def periodic_data_sending_task(self):
        # get controller handle to access server's working data
        controller_handle = self.server.get_controller_handle()
        # set data
        data = controller_handle.get_controller_message()
        if len(data) > 0:
            self.send_data_to(self.request, data)
            #print(f'[server] send to client: {message}')
        self.count -= 1

class IntegratedController(object):
    def __init__(self):
        self.samp_time = 0
        self.daq_controller = [AdamDaqController('daq_0', DAQ_0_IP, DAQ_0_PORT),  AdamDaqController('daq_1', DAQ_1_IP, DAQ_1_PORT)]
        #self.ztdr_controller = ZtdrController('ztdr', ZTDR_IP, ZTDR_PORT)
        self.virtual_daq_controller = VirtualDaqController('virtual_daq', VIRTUAL_DAQ_ROOT_PATH)
    def get_daq_controller(self, no=0):
        if no < 2:
            return self.daq_controller[no]


    def get_controller_message(self):
        message = {}
        '''
        ztdr_data = self.ztdr_controller.get_recent_data()
        if ztdr_data is not None:
            key = self.ztdr_controller.get_device_name()
            message[key] = ztdr_data
        '''
        '''
        for daq in self.daq_controller:
            daq_data = daq.get_recent_data()
            if daq_data is not None:
                key = daq.get_device_name()
                message[key] = daq_data
        '''
        vd = self.virtual_daq_controller.get_recent_data()
        if vd is not None:
            message['daq_0'] = [vd[5], vd[2], vd[4], 0, vd[3], vd[0], vd[1], 0]
            message['daq_1'] = [0, 0, 0, 0, 0, 0, 0, 0]

        return message

    def start(self):
        # start ztdr controller
        #self.ztdr_controller.start_send_timer(1.0)
        #self.ztdr_controller.start_receive_thread()
        # start two different daq controller
        for daq in self.daq_controller:
            daq.start_send_timer(0.1)
            daq.start_receive_thread()
        self.virtual_daq_controller.start_virtual_data_capture_timer(0.1)

    def stop(self):
        # stop ztdr controller
        #self.ztdr_controller.stop_send_timer()
        #self.ztdr_controller.stop_receive_thread()
        # stop all daq controller
        for daq in self.daq_controller:
            daq.stop_send_timer()
            daq.stop_receive_thread()
        self.virtual_daq_controller.stop_virtual_data_capture_timer()



host_ip = socket.gethostbyname(socket.gethostname())
port = 10000

controller = IntegratedController()
server = ThreadedTcpServer((host_ip, port), MyTcpHandler, controller)
server.start()
controller.start()
print("="*60)
print(f'TWO 8-CH DAQ TCP Server (ip:{host_ip}, port:{port}) is running')
print('Device names = [daq_0, daq_1]')
print("-"*60)
while True:
    time.sleep(1)
