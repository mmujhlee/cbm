import queue
import threading
import time
import socket
from ctypes import *
import struct
import numpy as np
import copy


class TdrParam():
    x = 0
    y = 0
    start = 0
    end = 10
    k = 2.25
    n = 1


class TdrData():
    data_no = 0
    x = np.zeros(1024, dtype=np.float32)
    y = np.zeros(1024, dtype=np.float32)


def float32_to_byte_big(val):
    bytedata = struct.pack('>f', val)
    return bytedata

def int32_to_byte_big(val):
    bytedata = struct.pack('>i', val)
    return bytedata

def int16_to_byte_big(val):
    bytedata = struct.pack('>h', val)
    return bytedata

def byte_to_float32_big(subdata):
    val = struct.unpack('>f', subdata)
    return val[0]

def byte_to_int16_big(subdata):
    # big endian
    val = c_int16(0xffff & ((subdata[0] << 8) & 0xff00) | subdata[1]).value
    return val


def byte_to_uint16_big(subdata):
    # big endian
    val = c_uint16(0xffff & ((subdata[0] << 8) & 0xff00) | subdata[1]).value
    return val


def byte_to_int32_big(subdata):
    # big endian
    val = (subdata[0] << 24) & 0xff000000
    val |= (subdata[1] << 16) & 0x00ff0000
    val |= (subdata[2] << 8) & 0x0000ff00
    val |= (subdata[3] & 0x000000ff)
    return c_int32(val).value


def byte_to_uint32_big(subdata):
    # big endian
    val = (subdata[0] << 24) & 0xff000000
    val |= (subdata[1] << 16) & 0x00ff0000
    val |= (subdata[2] << 8) & 0x0000ff00
    val |= (subdata[3] & 0x000000ff)
    return c_uint32(val).value

class ZtdrController(object):
    def __init__(self, device_name, ip_addr, port):
        # variables for thread-safe communication data
        self.thread_lock = threading.Lock()
        self.tdr_daq_data = None

        self.tdr_param_lock = threading.Lock()

        self.tdr_param = TdrParam()
        self.tdr_data = TdrData()

        self.is_thread_running = False
        self.is_daq_ready = False
        self.daq_capture_thread = None
        self.count = 0
        self._send_timer_handle = None
        self._send_timer_interval = -1  # default value is 1 sec for interval of data sending timer
        self._is_send_timer_alive = False
        self.ip_addr = ip_addr
        self.port = port

        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect((ip_addr, port))
        self.device_name = device_name

    def get_device_name(self):
        return self.device_name

    def get_recent_data(self):
        with self.thread_lock:
            return self.tdr_daq_data

    def write_current_data(self, data):
        with self.thread_lock:
            self.tdr_daq_data = copy.deepcopy(data)

    def start_send_timer(self, time_interval):
        self._is_send_timer_alive = True
        self._send_timer_interval = time_interval
        self._send_data_timer_fun()

    def stop_send_timer(self):
        self._is_send_timer_alive = False
        if self._send_timer_handle is not None:
            self._send_timer_handle.cancel()
            self._send_timer_handle.join()

    def set_tdr_control_parameters(self, params):
        if type(params) == dict:
            self.tdr_param.x = params['x']
            self.tdr_param.y = params['y']
            self.tdr_param.start = params['start']
            self.tdr_param.end = params['end']
            self.tdr_param.k = params['k']
            self.tdr_param.n = params['n']

    def _send_data_timer_fun(self):
        if self._is_send_timer_alive:

            #packet = bytearray(b'\x23\x0d\x0a')
            #self.client.send(packet)

            with self.tdr_param_lock:
                params = self.tdr_param

            '''
            tdr_param.x = 0
            tdr_param.y = 0
            tdr_param.start = 0
            tdr_param.end = 10
            tdr_param.k = 2.25
            tdr_param.n = 1
            '''
            packet = bytearray(b'\x23')
            packet += int16_to_byte_big(params.x)
            packet += int16_to_byte_big(params.y)
            packet += float32_to_byte_big(params.start)
            packet += float32_to_byte_big(params.end)
            packet += float32_to_byte_big(params.k)
            packet += int16_to_byte_big(params.n)
            packet += bytearray(b'\x0d\x0a')

            self.client.send(packet)

            # and reset timer event handler
            self._send_timer_handle = threading.Timer(self._send_timer_interval, self._send_data_timer_fun)
            self._send_timer_handle.daemon = True
            self._send_timer_handle.start()

    def daq_capture_thread_callback(self):
        while self.is_thread_running:

            if self.client:
                data = self.client.recv(10000)
                if len(data) == 8219:
                    idx = 1
                    tdr_data_no = byte_to_int32_big(data[idx:idx + 4])
                    idx += 4
                    self.tdr_param.x = byte_to_int16_big(data[idx:idx + 2])
                    idx += 2
                    self.tdr_param.y = byte_to_int16_big(data[idx:idx + 2])
                    idx += 2
                    self.tdr_param.start = byte_to_float32_big(data[idx:idx + 4])
                    idx += 4
                    self.tdr_param.end = byte_to_float32_big(data[idx:idx + 4])
                    idx += 4
                    self.tdr_param.k = byte_to_float32_big(data[idx:idx + 4])
                    idx += 4
                    self.tdr_param.n = byte_to_int16_big(data[idx:idx + 2])
                    idx += 2
                    self.tdr_param.rec = byte_to_int16_big(data[idx:idx + 2])
                    idx += 2

                    for k in range(1024):
                        self.tdr_data.x[k] = byte_to_float32_big(data[idx:idx + 4])
                        idx += 4
                    for k in range(1024):
                        self.tdr_data.y[k] = byte_to_float32_big(data[idx:idx + 4])
                        idx += 4

                    tmp_data = {}
                    tmp_data['x'] = list(self.tdr_data.x)
                    tmp_data['y'] = list(self.tdr_data.y)
                    self.write_current_data(tmp_data)

            time.sleep(0.001)

    def start_receive_thread(self):
        self.daq_capture_thread = threading.Thread(target=self.daq_capture_thread_callback)
        self.daq_capture_thread.daemon = True
        self.is_thread_running = True
        self.daq_capture_thread.start()

    def stop_receive_thread(self):
        if self.daq_capture_thread is not None:
            self.is_thread_running = False
            self.daq_capture_thread.join()
            self.daq_capture_thread = None

if __name__=='__main__':
    daq_ip = 'localhost'
    daq_port = 60000
    controller_handle = ZtdrController('ztdr', daq_ip, daq_port)
    controller_handle.start_send_timer(1.0)
    controller_handle.start_receive_thread()

    while True:
        frame = controller_handle.get_recent_data()
        if frame is not None:
            print(frame)
        time.sleep(1)
