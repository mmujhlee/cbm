import queue
import cv2
import threading
import time
from flirpy.camera.boson import Boson
import math
import numpy as np

import sys
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))

import thermal_image_utils.preprocessing as utils
import copy

# Camera driver used for CBM project
# The camera is composed of USB-type RGB camera and Flir Boson thermal camera

class CbmThermalCameraController(object):
    def __init__(self, device_name):

        # variables for data structure for storing
        self.thread_lock = threading.Lock()
        self.rgbt_image_data = None
        # variables for capture thread
        self.capture_thread = None
        self.is_thread_running = False
        # variables for rgb camera
        self.cap_rgb_camera = None
        self.is_rgb_camera_ready = False
        # variables for flir boson camera
        self.cap_boson_camera = None
        self.is_boson_camera_ready = False

        self.count = 0
        self.device_name = device_name

        # default homography matrix
        self.homography = np.array([[ 1.501535821, -0.007116104, -178.2189275],
                                    [-0.018119339,  1.420414333, -155.9713934],
                                    [-0.00014236,  -9.6391E-05,   1]])

    def get_device_name(self):
        return self.device_name

    def get_recent_data(self, is_one_encoded_image=True):
        image = self._get_recent_data()
        if image is not None:
            if is_one_encoded_image:
                rgb_frame = image['rgb']
                thermal_frame = image['thermal']
                encoded_gray_thermal_image = self.encode_rgbt_image(rgb_frame, thermal_frame)
                return encoded_gray_thermal_image
            return image
        return None

    def _get_recent_data(self):
        with self.thread_lock:
            return self.rgbt_image_data

    def write_current_data(self, data):
        with self.thread_lock:
            self.rgbt_image_data = copy.deepcopy(data)

    def image_capture(self):
        # initialize rgb camera capture device
        self.cap_rgb_camera = cv2.VideoCapture(0)
        if self.cap_rgb_camera.isOpened():
            self.is_rgb_camera_ready = True
        else:
            print('Connection Failure: Check RGB Camera Connection once again!!')

        # initialize flir boson camera capture device
        self.cap_boson_camera = Boson()
        if self.cap_boson_camera is not None:
            self.is_boson_camera_ready = True
        else:
            print('Connection failure: check FLIR Boson camera connection once again!!')

        while self.is_thread_running and self.is_rgb_camera_ready and self.is_boson_camera_ready:
            ret, rgb_frame = self.cap_rgb_camera.read()
            thermal_frame = self.cap_boson_camera.grab()
            two_img = {'rgb':rgb_frame, 'thermal':thermal_frame}

            # write current data to thread-safe variable
            self.write_current_data(two_img)

            time.sleep(0.03)
            self.count += 1

        self.cap_boson_camera.close()
        self.cap_rgb_camera.release()

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

    def encode_rgbt_image(self, rgb_image_640x480, thermal_image_320x256):

        t_img = utils.crop_boson_320x256_to_320x240(thermal_image_320x256)
        g_img = cv2.cvtColor(rgb_image_640x480, cv2.COLOR_BGR2GRAY)

        warp_image = cv2.warpPerspective(g_img, self.homography, (640, 480))
        g_img = cv2.resize(warp_image, (320, 240), interpolation=cv2.INTER_CUBIC)

        encoded_image = utils.encode_thermal_image(t_img)
        encoded_image[:, :, 2] = g_img
        return encoded_image

    def decode_rgbt_image(self, encoded_image):
        gray_image = encoded_image[:, :, 2]
        decoded_t = utils.decode_thermal_image(encoded_image)
        meta = utils.get_default_radiometry_parameters(RTemp=20)
        celsius_image = utils.raw2temp(decoded_t, meta)
        return gray_image, celsius_image

    def get_homography_matrix(self):
        return self.homography

    def set_homography_matrix(self, homography):
        self.homography = homography



if __name__ == '__main__':

    controller_handle = CbmThermalCameraController('image')
    controller_handle.start()

    try:
        while True:
            frame = controller_handle.get_recent_data()
            if frame is not None:
                cv2.imshow('encoded image', frame)

                gray_img, celsius_img = controller_handle.decode_rgbt_image(frame)
                colorized_img = utils.get_scaled_thermal_colormap(celsius_img, min_temp=np.min(celsius_img),
                                                                  max_temp=np.max(celsius_img))
                cv2.imshow('decoded gray_image', gray_img)
                cv2.imshow('decoded thermal image', colorized_img)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            time.sleep(0.03)
    finally:
        controller_handle.stop()
