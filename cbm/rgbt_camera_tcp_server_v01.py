import socket
import threading
import time
from base_socket.tcp_socket import ThreadedTcpServer, ThreadedTcpRequestHandler
import cv2
import queue
from cbm_sensor_devices.rgb_camera import RgbCameraController
from cbm_sensor_devices.flir_boson_camera import FlirBosonCameraController
from cbm_sensor_devices.cbm_thermal_camera.cbm_thermal_camera_driver import CbmThermalCameraController
import numpy as np

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
        # get controller handle to access server's working data
        controller_handle = self.server.get_controller_handle()
        # set messages
        data = {"data_0": self.count, "data_1": self.count}
        self.send_data_to(self.request, data)
        print(f'[server] send to client: {data}')
        self.count += 1

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
        #self.rgb_image_controller = RgbCameraController('rgb_image')
        #self.thermal_image_controller = FlirBosonCameraController('thermal_image')
        self.gt_image_controller = CbmThermalCameraController('gt_image')

    def get_controller_message(self):
        message = {}
        '''
        rgb_image = self.rgb_image_controller.get_recent_data()
        if rgb_image is not None:
            key = self.rgb_image_controller.get_device_name()
            message[key] = rgb_image

        thermal_image = self.thermal_image_controller.get_recent_data()
        if thermal_image is not None:
            key = self.thermal_image_controller.get_device_name()
            message[key] = thermal_image
        '''
        gt_image = self.gt_image_controller.get_recent_data()
        if gt_image is not None:
            key = self.gt_image_controller.get_device_name()
            message[key] = gt_image

        return message

    def start(self):
        # start image controller
        self.gt_image_controller.start()
        #self.rgb_image_controller.start()
        #self.thermal_image_controller.start()

    def stop(self):
        # stop image controller
        self.gt_image_controller.stop()
        #self.rgb_image_controller.stop()
        #self.thermal_image_controller.stop()

port = 10002
host_ip = socket.gethostbyname(socket.gethostname())

controller = IntegratedController()
server = ThreadedTcpServer((host_ip, port), MyTcpHandler, controller)
server.start()
controller.start()
print(f'Gray_Thermal Image Server (ip:{host_ip}, port:{port}) is running')

print("="*60)
print(f'Gray_Thermal Image Server (ip:{host_ip}, port:{port}) is running')
print('Device names = [rgb, thermal] or [gt_image]')
print("-"*60)

while True:
    time.sleep(1)
    #frame = controller_handle.image_queue.get()
    #cv2.imshow('capture image', frame)
    #print(controller_handle.image_queue.qsize())
    #cv2.waitKey(40)


#time.sleep(3)
#server.shutdown()
#print('close server')
