import queue
import threading
import time
import socket
import copy

class AdamDaqController(object):
    def __init__(self, device_name, ip_addr, port):

        self.thread_lock = threading.Lock()
        self.adam_daq_data = None

        self.is_thread_running = False
        self.is_daq_ready = False
        self.daq_capture_thread = None
        self.count = 0
        self._send_timer_handle = None
        self._send_timer_interval = -1  # default value is 1 sec for interval of data sending timer
        self._is_send_timer_alive = False
        self.ip_addr = ip_addr
        self.port = port

        self.client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.device_name = device_name

    def get_device_name(self):
        return self.device_name

    def get_recent_data(self):
        with self.thread_lock:
            return self.adam_daq_data

    def write_current_data(self, data):
        with self.thread_lock:
            self.adam_daq_data = copy.deepcopy(data)

    def start_send_timer(self, time_interval):
        self._is_send_timer_alive = True
        self._send_timer_interval = time_interval
        self._send_data_timer_fun()

    def stop_send_timer(self):
        self._is_send_timer_alive = False
        if self._send_timer_handle is not None:
            self._send_timer_handle.cancel()
            self._send_timer_handle.join()

    def _send_data_timer_fun(self):
        if self._is_send_timer_alive:

            packet = b'#01' + b'\x0d'
            self.client.sendto(packet, (self.ip_addr, self.port))

            # and reset timer event handler
            self._send_timer_handle = threading.Timer(self._send_timer_interval, self._send_data_timer_fun)
            self._send_timer_handle.daemon = True
            self._send_timer_handle.start()

    def daq_capture_thread_callback(self):
        while self.is_thread_running:

            if self.client:
                data = self.client.recvfrom(1024)
                str_data = data[0][1:-1]
                str_data = str_data.decode()

                daq_data = []
                for k in range(9):
                    # +00.000 : length
                    daq_data.append(float(str_data[k * 7: (k + 1) * 7]))

                # write current data to class variable
                self.write_current_data(daq_data)

                time.sleep(0.01)

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
    daq_ip = '192.168.0.200'
    daq_port = 1025
    controller_handle = AdamDaqController(daq_ip, daq_port)
    controller_handle.start_send_timer(1.0)
    controller_handle.start_receive_thread()

    while True:
        frame = controller_handle.get_recent_data()
        if frame is not None:
            print(frame)
        time.sleep(0.1)
