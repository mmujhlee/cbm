import queue
import cv2
import threading
import time
import copy

class RgbCameraController(object):
    def __init__(self, device_name):
        self.thread_lock = threading.Lock()
        self.rgb_image_data = None

        self.is_thread_running = False
        self.is_camera_ready = False
        self.capture_thread = None
        self.count = 0
        self.device_name = device_name

    def get_device_name(self):
        return self.device_name

    def get_recent_data(self):
        with self.thread_lock:
            return self.rgb_image_data

    def write_current_data(self, data):
        with self.thread_lock:
            self.rgb_image_data = copy.deepcopy(data)

    def image_capture(self):
        capture_device = cv2.VideoCapture(0)
        if not capture_device.isOpened():
            print('Connection Failure: Check Camera Connection!!')
        else:
            self.is_camera_ready = True

        while self.is_thread_running and self.is_camera_ready:
            ret, frame = capture_device.read()

            if ret:
                # write current image frame to self.rgb_image_data
                self.write_current_data(frame)

            time.sleep(0.03)
            self.count += 1


    def start(self):
        self.capture_thread = threading.Thread(target=self.image_capture)
        self.capture_thread.daemon = True
        self.is_thread_running = True
        self.capture_thread.start()

    def stop(self):
        if self.capture_thread is not None:
            self.is_thread_running = False
            self.capture_thread.join()
            self.capture_thread = None

if __name__=='__main__':
    controller_handle = RgbCameraController('image')
    controller_handle.start()

    while True:
        frame = controller_handle.get_recent_data()
        if frame is not None:
            cv2.imshow('capture image', frame)
            cv2.waitKey(40)
