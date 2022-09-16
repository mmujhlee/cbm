import queue
import threading
import time
import socket
import os
import pandas as pd
import numpy as np
import copy

class VirtualDaqController(object):
    def __init__(self, device_name, filepath):
        # variables for thread-safe communication data
        self.thread_lock = threading.Lock()
        self.virtual_daq_data = None

        self.is_thread_running = False
        self.is_daq_ready = False
        self.daq_capture_thread = None
        self.count = 0
        self._send_timer_handle = None
        self._send_timer_interval = -1  # default value is 1 sec for interval of data sending timer
        self._is_send_timer_alive = False

        self.current_data_index = 0
        self.max_data_index = 0
        self.virtual_data_x = None
        self.virtual_data_y = None

        #self.client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.device_name = device_name
        self.virtual_data_x, self.virtual_data_y = self.load_virtual_daq_data(filepath)
        self.max_data_index = self.virtual_data_x.shape[0]

    def load_virtual_daq_data(self, filepath):
        root_path = filepath
        labels = ['000', '010', '020', '030', '040', '050', '060', '070', '080', '090', '100']

        data_dic = {}
        g_data_list = []
        all_data = np.array([])
        all_label = np.array([])

        for a_file in os.listdir(root_path):
            file_name = os.path.join(root_path, a_file)
            print(file_name)
            df = pd.read_excel(file_name)
            label = df['label'][0]
            timestamp = df.iloc[:, 0].values
            x_data = df.iloc[:, 1:-1].values
            y_data = df.iloc[:, -1].values

            all_data = np.concatenate((all_data.reshape(-1, x_data.shape[1]), x_data))
            all_label = np.concatenate((all_label.reshape(-1, ), y_data))
        return all_data, all_label

    def get_device_name(self):
        return self.device_name

    def get_recent_data(self):
        with self.thread_lock:
            return self.virtual_daq_data

    def write_current_data(self, data):
        with self.thread_lock:
            self.virtual_daq_data = copy.deepcopy(data)

    def start_virtual_data_capture_timer(self, time_interval):
        self._is_send_timer_alive = True
        self._send_timer_interval = time_interval
        self._virtual_data_capture_timer_fun()

    def stop_virtual_data_capture_timer(self):
        self._is_send_timer_alive = False
        if self._send_timer_handle is not None:
            self._send_timer_handle.cancel()
            self._send_timer_handle.join()

    def _virtual_data_capture_timer_fun(self):
        if self._is_send_timer_alive:

            if self.current_data_index < self.max_data_index:
                daq_data = list(self.virtual_data_x[self.current_data_index, :])

                # write currenet daq data to self.daq_data
                self.write_current_data(daq_data)

            if self.current_data_index < self.max_data_index:
                self.current_data_index += 1
            else:
                self.current_data_index = 0

            # and reset timer event handler
            self._send_timer_handle = threading.Timer(self._send_timer_interval, self._virtual_data_capture_timer_fun)
            self._send_timer_handle.daemon = True
            self._send_timer_handle.start()

if __name__=='__main__':

    rootpath = 'daq_training_data'
    controller = VirtualDaqController('virtual_daq', rootpath)
    controller.start_virtual_data_capture_timer(0.1)

    while True:
        frame = controller.get_recent_data()
        if frame is not None:
            print(frame)
        time.sleep(0.1)
