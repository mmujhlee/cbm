import socket
import queue
import time
import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot
from PyQt5 import QtWidgets
import cv2

import sys
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))

from base_socket.tcp_socket import TcpClient
from cbm_gui.cbm_dashboard_widget import CBM_DashboardWidget

UI_FILE_DIR = "cbm_gui/dashboard.ui"

import datetime

class MyTcpClient(TcpClient, QThread):
    _steam_msg = None
    _test_msg = None
    _steam_sys_adc = []
    _sw_sys_adc = []
    _count = 0

    '''
    # for thermal camera (FLIR Boson)
    _sub_thermal_image_raw = None
    _msg_thermal_image = None
    _signal_t_image_received = pyqtSignal(np.ndarray)

    # for RGB Camera (USB Camera)
    _sub_rgb_image_raw = None
    _msg_rgb_image = None
    _signal_rgb_image_received = pyqtSignal(np.ndarray)
    '''
    _sub_gt_image_raw = None
    _msg_gt_image = None
    _signal_gt_image_received = pyqtSignal(np.ndarray)

    # for Raspi-based DAG installed in steam pipe line
    _sub_steam_sys_adc = None
    _msg_steam_sys_adc = None
    _signal_steam_sys_adc_received = pyqtSignal(list)

    # for Raspi-based DAG installed in seawater pipe line
    _sub_sw_sys_adc = None
    _msg_sw_sys_adc = None
    _signal_sw_sys_adc_received = pyqtSignal(list)

    # for TDR Sensor to detect seawater pipe leakage
    _sub_tdr_sensor_sys = None
    _msg_tdr_sensor_sys = None
    _signal_tdr_sensor_sys_received = pyqtSignal(dict)

    _sub_clogging_infer_sys = None
    _msg_clogging_infer_sys = None
    _signal_clogging_infer_sys_received = pyqtSignal(int)

    '''
    rgb_image_queue = queue.Queue()
    thermal_image_queue = queue.Queue()
    '''
    gt_image_queue = queue.Queue()

    daq_0_queue = queue.Queue()
    daq_1_queue = queue.Queue()
    _max_q_size = 20

    def __init__(self, ip_address, port_no):
        TcpClient.__init__(self, ip_address, port_no)
        QThread.__init__(self)

    def write_to_file(self, filename, data):
        try:
            #print(filename, data)
            with open(filename, 'w') as p:
                p.writelines(data)
            print(filename, data)
        except IOError as e:
            pass

    def request_periodic_data_sending(self, interval):
        data = {"cmd": 'start', 'interval': interval}
        self.send_data_to_server(data)
        print(f'[client] sending to server: {data}')

    def data_sending_task(self):
        data = {"cmd": 'once', "body": {"msg": "This is a test."}}
        self.send_data_to_server(data)
        print(f'[client] sending to server: {data}')

    def data_received_task(self, data):
        if data:
            if type(data) is dict:
                if 'gt_image' in data.keys():
                    if self.gt_image_queue.qsize() > self._max_q_size:
                        _ = self.gt_image_queue.get()
                    self.gt_image_queue.put(data['gt_image'])
                    self.gt_image_callback(data['gt_image'])
                '''
                if 'rgb_image' in data.keys():
                    if self.rgb_image_queue.qsize() > self._max_q_size:
                        _ = self.rgb_image_queue.get()
                    self.rgb_image_queue.put(data['rgb_image'])
                    self.rgb_image_callback(data['rgb_image'])
                
                if 'thermal_image' in data.keys():
                    if self.thermal_image_queue.qsize() > self._max_q_size:
                        _ = self.thermal_image_queue.get()
                    self.thermal_image_queue.put(data['thermal_image'])
                    self.thermal_image_callback(data['thermal_image'])
                '''
                if 'daq_0' in data.keys():
                    if self.daq_0_queue.qsize() > self._max_q_size:
                        _ = self.daq_0_queue.get()
                    self.daq_0_queue.put(data['daq_0'])
                    self.sw_sys_callback(data['daq_0'])
                if 'daq_1' in data.keys():
                    if self.daq_1_queue.qsize() > self._max_q_size:
                        _ = self.daq_1_queue.get()
                    self.daq_1_queue.put(data['daq_1'])
                    self.steam_sys_callback(data['daq_1'])
                if 'ztdr' in data.keys():
                    self.tdr_sensor_sys_callback(data['ztdr'])

                if 'infer_clogging' in data.keys():
                    self.clogging_infer_sys_callback(data['infer_clogging'])

            elif type(data) is bytes:
                print(f'[client] receiving from server: {data}')

    def clogging_infer_sys_callback(self, msg):
        self._msg_clogging_infer_sys = msg
        self._signal_clogging_infer_sys_received.emit(self._msg_clogging_infer_sys)

    def steam_sys_callback(self, msg):
        self._msg_steam_sys_adc = msg
        # self._steam_sys_adc = [msg.ch0, msg.ch1, msg.ch2, msg.ch3, msg.ch4, msg.ch5, msg.ch6, msg.ch7]
        self._signal_steam_sys_adc_received.emit(self._msg_steam_sys_adc)

    def sw_sys_callback(self, msg):
        self._msg_sw_sys_adc = msg
        # self._sw_sys_adc = [msg.ch0, msg.ch1, msg.ch2, msg.ch3, msg.ch4, msg.ch5, msg.ch6, msg.ch7]
        self._signal_sw_sys_adc_received.emit(self._msg_sw_sys_adc)
        #print("sw:", self._msg_sw_sys_adc)

        file_prefix =  '/cbm/data/SW PIPE_' # name the folder
        # 아래 수정 필요함.
        #str_time = datetime.datetime().strftime("%Y_%m_%dT_%H_%M_%S")

        current_time = datetime.datetime.today()  # 2021-08-15 20:58:43.302125
        str_time = current_time.strftime('%Y%m%d%H%M%S')

        print(str_time)
        filename = '%s%s.csv' % (file_prefix, str_time)
        self._count += 1
        str_data = ''
        for ele in self._msg_sw_sys_adc:
            str_data += '%f, ' % ele
        self.write_to_file(filename, str_data)
    '''
    def thermal_image_callback(self, msg):
        self._msg_thermal_image = msg
        self._signal_t_image_received.emit(self._msg_thermal_image)

    def rgb_image_callback(self, msg):
        self._msg_rgb_image = msg
        self._signal_rgb_image_received.emit(self._msg_rgb_image)
    '''

    def gt_image_callback(self, msg):
        self._msg_gt_image = msg
        self._signal_gt_image_received.emit(self._msg_gt_image)

    def tdr_sensor_sys_callback(self, msg):
        self._msg_tdr_sensor_sys = msg
        self._signal_tdr_sensor_sys_received.emit(self._msg_tdr_sensor_sys)

    def get_steam_sys_adc_msg(self):
        return self._msg_steam_sys_adc

    def get_sw_sys_adc_msg(self):
        return self._msg_sw_sys_adc

    def get_thermal_image_msg(self):
        return self._msg_thermal_image

    def get_rgb_image_msg(self):
        return self._msg_rgb_image

    def get_tdr_sensor_sys_msg(self):
        return self._msg_tdr_sensor_sys

    def display_received_messages(self):
        image = None
        daq_0 = None
        daq_1 = None

        while self.rgb_image_queue.qsize() > 0:
            image = self.rgb_image_queue.get()

        while self.daq_0_queue.qsize() > 0:
            daq_0 = self.daq_0_queue.get()

        while self.daq_1_queue.qsize() > 0:
            daq_1 = self.daq_1_queue.get()

        if image is not None:
            cv2.imshow('capture image', image)
            cv2.waitKey(1)

        if daq_0 is not None:
            print(f'daq 0: {daq_0}')
        if daq_1 is not None:
            print(f'daq 1: {daq_1}')


if __name__ == '__main__':
    '''
    ip = socket.gethostbyname(socket.gethostname())
    #ip = '192.168.0.17'
    port = 9999

    client = MyTcpClient(ip, port)
    # client.start_send_timer(1.0)
    client.request_periodic_data_sending(0.1)
    client.start_received_thread()
    '''
    server_ip = '172.17.0.2' # ip of container
    #server_ip = '172.30.1.58'

    #server_ip = socket.gethostbyname(socket.gethostname())

    daq_ip = server_ip
    daq_port = 10000

    ztdr_ip = server_ip
    ztdr_port = 10001

    camera_ip = server_ip
    camera_port = 10002

    clogging_infer_ip = socket.gethostbyname(socket.gethostname())
    clogging_infer_port = 10003

    daq_client = MyTcpClient(daq_ip, daq_port)
    ztdr_client = MyTcpClient(ztdr_ip, ztdr_port)
    camera_client = MyTcpClient(camera_ip, camera_port)
    clogging_infer_client = MyTcpClient(clogging_infer_ip, clogging_infer_port)

    thermal_map_file = 'cbm_sensor_devices/cbm_thermal_camera/trained_thermal_map.xlsx'
    app = QtWidgets.QApplication(sys.argv)
    '''
    myWindow = CBM_DashboardWidget(UI_FILE_DIR, daq_client=daq_client,
                                                ztdr_client=ztdr_client,
                                                camera_client=camera_client,
                                                clogging_infer_client=clogging_infer_client)
    '''
    myWindow = CBM_DashboardWidget(UI_FILE_DIR, daq_client=daq_client)

    myWindow.set_thermal_map_from_file(thermal_map_file)
    myWindow.show()
    app.exec_()

    '''
    while True:
        client.display_received_messages()
        time.sleep(1)
    '''
    #client.close()

