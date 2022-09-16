import sys
from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot
import time
import numpy as np

'''
import rclpy
from rclpy.node import Node
from std_msgs.msg import Header
from sensor_msgs.msg import Image
from cbm_interfaces.msg import AdcRaspi
from cbm_interfaces.msg import TdrSensor
'''

class QAmsListenerNode(QThread):
    _steam_msg = None
    _test_msg = None
    _steam_sys_adc = []
    _sw_sys_adc = []

    # for thermal camera (FLIR Boson)
    _sub_thermal_image_raw = None
    _msg_thermal_image = None
    _signal_t_image_received = pyqtSignal(np.ndarray)
    
    # for RGB Camera (USB Camera)
    _sub_rgb_image_raw = None
    _msg_rgb_image = None
    _signal_rgb_image_received = pyqtSignal(np.ndarray)

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
    _signal_tdr_sensor_sys_received = pyqtSignal(np.ndarray)

    def __init__(self):

        Node.__init__(self, 'Alarm_and_Monitoring_System')
        QThread.__init__(self)
        '''
        self._sub_steam_sys_adc = self.create_subscription(AdcRaspi, '/steam_line/adc_8ch', self.steam_sys_callback, 10)
        self._sub_sw_sys_adc = self.create_subscription(AdcRaspi, '/test_sys/adc_8ch', self.sw_sys_callback, 10)
        self._sub_thermal_image_raw = self.create_subscription(Image,'/t_image_raw', self.thermal_image_callback, 10)
        self._sub_rgb_image_raw = self.create_subscription(Image,'/rgb_image_raw', self.rgb_image_callback, 10)
        self._sub_tdr_sensor_sys = self.create_subscription(TdrSensor,'/tdr_sensor', self.tdr_sensor_sys_callback, 10)
        '''
    def __del__(self):
        self.wait()

    def steam_sys_callback(self, msg):
        self._msg_steam_sys_adc = msg
        #self._steam_sys_adc = [msg.ch0, msg.ch1, msg.ch2, msg.ch3, msg.ch4, msg.ch5, msg.ch6, msg.ch7] 
        self._signal_steam_sys_adc_received.emit(self._msg_steam_sys_adc)

    def sw_sys_callback(self, msg):
        self._msg_sw_sys_adc = msg
        #self._sw_sys_adc = [msg.ch0, msg.ch1, msg.ch2, msg.ch3, msg.ch4, msg.ch5, msg.ch6, msg.ch7] 
        self._signal_sw_sys_adc_received.emit(self._msg_sw_sys_adc)
        #print("sw:", msg.ch0)

    def thermal_image_callback(self, msg):
        self._msg_thermal_image = msg
        self._signal_t_image_received.emit(self._msg_thermal_image)

    def rgb_image_callback(self, msg):
        self._msg_rgb_image = msg
        self._signal_rgb_image_received.emit(self._msg_rgb_image)

    def tdr_sensor_sys_callback(self, msg):
        self._msg_tdr_sensor_sys = msg
        self._signal_tdr_sensor_sys_received.emit(self._msg_tdr_sensor_sys)

    def run(self):
        while True:
            #rclpy.spin_once(self)
            #print("-"*20)
            #self.emit( QtCore.SIGNAL('update(QString)'), "from work thread " + str(i) ) # example 
            time.sleep(0.01)
        self.terminate()

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