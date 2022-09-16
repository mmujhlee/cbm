import cbm_thermal_camera_driver as camera_driver
import thermal_image_utils.preprocessing as utils

import numpy as np
import cv2
import matplotlib.pyplot as plt
from matplotlib.colors import LightSource
import time
from matplotlib import cm
import os



# several environment variables for saving as file
#save_root_dir = './image/'
save_root_dir = 'rgbt_images_for_training'
save_file_prefix = 'rgbt_img'
save_file_interval = 10  # 캡쳐 10번에 1번 저장

controller_handle = camera_driver.CbmThermalCameraController('image')
controller_handle.start()
meta = utils.get_default_radiometry_parameters(RTemp=20)


old_frame_count = 0

old_time = 0
image_count = 0
save_file_no = 0
try:
    while True:
        frame = controller_handle.get_recent_data(is_one_encoded_image=False)
        if frame is not None:
            t_img_orig = frame['thermal']
            encoded_t_image = utils.encode_thermal_image(t_img_orig)
            rgb_image = frame['rgb']

            color_width = rgb_image.shape[1]
            color_height = rgb_image.shape[0]
            thermal_width = encoded_t_image.shape[1]
            thermal_height = encoded_t_image.shape[0]
            saved_image = np.zeros((color_height, color_width+thermal_width, 3), dtype=np.uint8)
            saved_image[:color_height, :color_width, :] = rgb_image
            saved_image[:thermal_height, color_width:, :] = encoded_t_image

            if image_count % save_file_interval == 0:
                # make directory to save image files
                try:
                    if not os.path.isdir(save_root_dir):
                        os.mkdir(save_root_dir)
                except OSError as error:
                    print(error)

                # make file name and save it into the save directory
                number = '%d' % save_file_no
                file_name = "%s_%s.png" % (save_file_prefix, number.zfill(10))
                save_file_no += 1

                save_file_name = os.path.join(save_root_dir, file_name)
                cv2.imwrite(save_file_name, saved_image)

                # display capture signal on the captued
                saved_image = cv2.rectangle(saved_image, (0,0), (color_width+thermal_width, color_height), (0, 0, 255), 3)

            image_count += 1

            # Show images
            cv2.namedWindow('saved image', cv2.WINDOW_AUTOSIZE)
            cv2.imshow('saved image', saved_image)

            if cv2.waitKey(33) & 0xFF == ord('q'):
                break
finally:
    controller_handle.stop()
