import os
from PyQt5 import uic
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import *
import pandas as pd

import time
import threading
import cv2
from queue import Queue
import numpy as np

import sys
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))

from analoggaugewidget import *
import cbm_sensor_devices.cbm_thermal_camera.thermal_image_utils.preprocessing as utils

running = False

class MyImageWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(MyImageWidget, self).__init__(parent)
        self.image = None

    def setImage(self, image):
        self.image = image
        sz = image.size()
        self.setMinimumSize(sz)
        self.update()

    def paintEvent(self, event):
        qp = QtGui.QPainter()
        qp.begin(self)
        if self.image:
            qp.drawImage(QtCore.QPoint(0, 0), self.image)
        qp.end()

class CBM_DashboardWidget(QtWidgets.QMainWindow):

    _saved_adc_file_full_name = ""
    _is_running_adc_acquisition_thread = False
    _adc_acquisition_thread = None
    _adc_acquisition_sampling_time = 100
    _image_widget_frame_size = None
    tcp_client = None
    _ros_thread = None
    _is_running_ros_thread = None

    def __init__(self, ui_file, daq_client=None, ztdr_client=None,
                                camera_client=None, clogging_infer_client=None):

        super(QMainWindow, self).__init__()
        # uic.loadUi('dashboard.ui', self)
        uic.loadUi(ui_file, self)

        self.thermal_map = None

        # store tcp client handle
        self.daq_client = daq_client
        self.ztdr_client = ztdr_client
        self.camera_client = camera_client
        self.clogging_infer_client = clogging_infer_client

        # for connecting to ROS system
        self.pushButton_connect_to_ros.clicked.connect(self.connect_to_ros)
        self.pushButton_disconnect.clicked.connect(self.disconnect_ros)

        # for strainer clogging
        self.progressBar_clogging.setValue(100)

        # for data acquision
        self.pushButton_save_path.clicked.connect(self.open_file_dialog)
        self.pushButton_acquisition_start.clicked.connect(self.start_adc_acquisition_task)
        self.pushButton_acquisition_stop.clicked.connect(self.stop_adc_acquisition_task)

        self.edt_file_prefix.setText("adc_data")
        self.spinBox_sampling_period.setValue(200)
        self.edt_save_file_name.setText("Please chose save file directory!!")
        self.edt_save_file_name.setReadOnly(True)

        self.gauge_widget_pump_load.value_min = 0.0
        self.gauge_widget_pump_load.value_max = 5.0
        self.gauge_widget_pump_load.update_value(0.0)

        self.gauge_widget_pump_out_pres.value_min = 0.0
        self.gauge_widget_pump_out_pres.value_max = 5.0
        self.gauge_widget_pump_out_pres.update_value(0.0)

        self.gauge_widget_sw_temp.value_min = 0.0
        self.gauge_widget_sw_temp.value_max = 5.0
        self.gauge_widget_sw_temp.update_value(0.0)

        self.gauge_widget_pipe_corosion.value_min = 0.0
        self.gauge_widget_pipe_corosion.value_max = 5.0
        self.gauge_widget_pipe_corosion.update_value(0.0)

        self.gauge_widget_strainer_diff.value_min = 0.0
        self.gauge_widget_strainer_diff.value_max = 5.0
        self.gauge_widget_strainer_diff.update_value(0.0)

        self.gauge_widget_strainer_inlet_pres.value_min = 0.0
        self.gauge_widget_strainer_inlet_pres.value_max = 5.0
        self.gauge_widget_strainer_inlet_pres.update_value(0.0)

        self.gauge_widget_pipe_strainer_outlet_pres.value_min = 0.0
        self.gauge_widget_pipe_strainer_outlet_pres.value_max = 5.0
        self.gauge_widget_pipe_strainer_outlet_pres.update_value(0.0)

        self.gauge_widget_reserved.value_min = 0.0
        self.gauge_widget_reserved.value_max = 5.0
        self.gauge_widget_reserved.update_value(0.0)

        self.gauge_widget_room_temp.value_min = 0.0
        self.gauge_widget_room_temp.value_max = 5.0
        self.gauge_widget_room_temp.update_value(0.0)

        self.gauge_widget_room_humidity.value_min = 0.0
        self.gauge_widget_room_humidity.value_max = 5.0
        self.gauge_widget_room_humidity.update_value(0.0)

        self.gauge_widget_pipe_surface_temp.value_min = 0.0
        self.gauge_widget_pipe_surface_temp.value_max = 5.0
        self.gauge_widget_pipe_surface_temp.update_value(0.0)

        self.gauge_widget_room_cui_sensor.value_min = 0.0
        self.gauge_widget_room_cui_sensor.value_max = 5.0
        self.gauge_widget_room_cui_sensor.update_value(0.0)

        self.plot_widget_tdr_original.showGrid(x=True, y=True)
        self.plot_widget_tdr_original.setLabel('left', 'Volt', units='mV')
        self.plot_widget_tdr_original.setLabel('bottom', 'Round trip', units='m')
        #self.plot_widget_tdr_original.setXRange(0, 10.0)
        #self.plot_widget_tdr_original.setYRange(0, 5.0)

        self.plot_widget_tdr_detection.showGrid(x=True, y=True)
        self.plot_widget_tdr_detection.setLabel('left', 'Volt', units='mV')
        self.plot_widget_tdr_detection.setLabel('bottom', 'Round trip', units='m')
        #self.plot_widget_tdr_detection.setXRange(0, 10.0)
        #self.plot_widget_tdr_detection.setYRange(0, 5.0)

        # for displaying RGBT image
        self._image_widget_frame_size = (self.image_widget_thermal.frameSize().width(), self.image_widget_thermal.frameSize().height())
        self.image_widget_thermal = MyImageWidget(self.image_widget_thermal)
        self.image_widget_reconstructed = MyImageWidget(self.image_widget_reconstructed)

        if self.daq_client is not None:
            self.daq_client._signal_steam_sys_adc_received.connect(self.on_steam_sys_adc_received)
            self.daq_client._signal_sw_sys_adc_received.connect(self.on_sw_sys_adc_received)

        if self.ztdr_client is not None:
            self.ztdr_client._signal_tdr_sensor_sys_received.connect(self.on_tdr_sensor_sys_received)

        if self.camera_client is not None:
            #self.camera_client._signal_t_image_received.connect(self.on_thermal_image_received)
            #self.camera_client._signal_rgb_image_received.connect(self.on_rgb_image_received)
            self.camera_client._signal_gt_image_received.connect(self.on_gt_image_received)

        if self.clogging_infer_client is not None:
            self.clogging_infer_client._signal_clogging_infer_sys_received.connect(self.on_clogging_infer_sys_received)

    def set_thermal_map_from_file(self, thermal_map_file):
        try:
            self.thermal_map = pd.read_excel(thermal_map_file, header=None).to_numpy()
        except IOError as e:
            self.thermal_map = None


    def on_steam_sys_adc_received(self, adc_msg):
        self.gauge_widget_room_temp.update_value(adc_msg[0])
        self.gauge_widget_room_humidity.update_value(adc_msg[1])
        self.gauge_widget_pipe_surface_temp.update_value(adc_msg[2])
        self.gauge_widget_room_cui_sensor.update_value(adc_msg[3])

    def on_sw_sys_adc_received(self, adc_msg):
        self.gauge_widget_pump_load.update_value(adc_msg[0])
        self.gauge_widget_pump_out_pres.update_value(adc_msg[1])
        self.gauge_widget_sw_temp.update_value(adc_msg[2])
        self.gauge_widget_pipe_corosion.update_value(adc_msg[3])
        self.gauge_widget_strainer_diff.update_value(adc_msg[4])
        self.gauge_widget_strainer_inlet_pres.update_value(adc_msg[5])
        self.gauge_widget_pipe_strainer_outlet_pres.update_value(adc_msg[6])
        self.gauge_widget_reserved.update_value(adc_msg[7])

    def on_gt_image_received(self, image_msg):
        self.update_gt_image_frames(image_msg)

    def on_tdr_sensor_sys_received(self, tdr_msg):
        x = tdr_msg['x']
        y = tdr_msg['y']
        self.plot_widget_tdr_original.plot(x, y, clear=True)

    def on_clogging_infer_sys_received(self, clogging_msg):
        label = clogging_msg
        if label >=0 and label <= 10:
            self.progressBar_clogging.setValue(label*10)

    def connect_to_ros(self):
        print('Connect to CBM Network')
        if self.daq_client is not None:
            self.daq_client.connect()
            self.daq_client.start_received_thread()
            self.daq_client.request_periodic_data_sending(1.0)

        if self.ztdr_client is not None:
            self.ztdr_client.connect()
            self.ztdr_client.start_received_thread()
            self.ztdr_client.request_periodic_data_sending(1.0)

            tdr_params ={}
            tdr_params['x'] = 0
            tdr_params['y'] = 0
            tdr_params['start'] = 5
            tdr_params['end'] = 9
            tdr_params['k'] = 2.25
            tdr_params['n'] = 1
            data = {'cmd':'set_params', 'params':tdr_params}
            self.ztdr_client.send_data_to_server(data)


        if self.camera_client is not None:
            self.camera_client.connect()
            self.camera_client.start_received_thread()
            self.camera_client.request_periodic_data_sending(1.0)

        if self.clogging_infer_client is not None:
            self.clogging_infer_client.connect()
            self.clogging_infer_client.start_received_thread()
            self.clogging_infer_client.request_periodic_data_sending(1)

    def disconnect_ros(self):
        if self.daq_client is not None:
            self.daq_client.disconnect()

        if self.ztdr_client is not None:
            self.ztdr_client.disconnect()

        if self.camera_client is not None:
            self.camera_client.disconnect()

        if self.clogging_infer_client is not None:
            self.clogging_infer_client.disconnect()


    def open_file_dialog(self):
        home_dir = os.path.expanduser('~')
        dir_path = QFileDialog.getExistingDirectory(self, "Choose Directory", home_dir)
        file_name = self.edt_file_prefix.text() + '.csv'
        self._saved_adc_file_full_name = os.path.join(os.sep, dir_path, file_name)
        self.edt_save_file_name.setText("save file name : \n" + self._saved_adc_file_full_name)

    def start_adc_acquisition_task(self):
        self._adc_acquisition_sampling_time = 0.001 * float(self.spinBox_sampling_period.value())
        self.edt_save_file_name.setText("Now save data into the file:\n" + self._saved_adc_file_full_name)

        self._is_running_adc_acquisition_thread = True
        self._adc_acquisition_thread = threading.Thread(target=self.adc_data_acquisition_thread_fun)
        self._adc_acquisition_thread.daemon = True
        self._adc_acquisition_thread.start()

    def stop_adc_acquisition_task(self):
        self.edt_save_file_name.setText("File saved. Please check:\n" + self._saved_adc_file_full_name)
        self._is_running_adc_acquisition_thread = False

    def adc_data_acquisition_thread_fun(self):
        if len(self._saved_adc_file_full_name) > 0:
            file = open(self._saved_adc_file_full_name, 'w')
            if file is not None:
                while self._is_running_adc_acquisition_thread:
                    sw_msg = self.ros_thread.get_sw_sys_adc_msg()
                    steam_msg = self.ros_thread.get_steam_sys_adc_msg()
                    if sw_msg is not None and steam_msg is not None:
                        #print("data acquisition for every %f" % self._adc_acquisition_sampling_time)
                        str_txt = "%f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f\n" % (sw_msg.ch0, sw_msg.ch1, sw_msg.ch2, sw_msg.ch3,
                                                                                    sw_msg.ch4, sw_msg.ch5, sw_msg.ch6, sw_msg.ch7,  
                                                                                    steam_msg.ch0, steam_msg.ch1, steam_msg.ch2, steam_msg.ch3)
                        file.writelines(str_txt)
                    else:
                        print("cannot write file. please check all daq status")
                        break
                    time.sleep(self._adc_acquisition_sampling_time)

                file.close()

    def update_gt_image_frames(self, gt_image):
        if gt_image is not None:

            g_image, celsius_image = utils.decode_rgbt_image(gt_image)
            colorized_img = utils.get_scaled_thermal_colormap(celsius_image, min_temp=np.min(celsius_image), max_temp=np.max(celsius_image))
            self.fit_and_draw_image(self.image_widget_thermal, colorized_img)

            if self.thermal_map is not None:
                overlaied_image = utils.get_overlaied_image(g_image, celsius_image, self.thermal_map)
                self.fit_and_draw_image(self.image_widget_reconstructed, overlaied_image)

    def fit_and_draw_image(self, target_widget, image):
        img_height = image.shape[0]
        img_width = image.shape[1]
        (frame_width, frame_height) = self._image_widget_frame_size
        scale_w = float(frame_width) / float(img_width)
        scale_h = float(frame_height) / float(img_height)
        scale = min([scale_w, scale_h])

        if scale == 0:
            scale = 1

        img = cv2.resize(image, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

        if len(image.shape) == 2:
            print(image.shape)
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
        else:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        height, width, bpc = img.shape
        bpl = bpc * width
        image = QtGui.QImage(img.data, width, height, bpl, QtGui.QImage.Format_RGB888)
        target_widget.setImage(image)

    def closeEvent(self, event):
        """Generate 'question' dialog on clicking 'X' button in title bar.

        Reimplement the closeEvent() event handler to include a 'Question'
        dialog with options on how to proceed - Save, Close, Cancel buttons
        """
        reply = QMessageBox.question(
            self, "Message",
            "Are you sure you want to quit?", QMessageBox.Close | QMessageBox.Cancel)

        if reply == QMessageBox.Close:
            event.accept()
        else:
            event.ignore()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    ui_file = 'dashboard.ui'
    myWindow = CBM_DashboardWidget(ui_file)
    myWindow.show()
    app.exec_()