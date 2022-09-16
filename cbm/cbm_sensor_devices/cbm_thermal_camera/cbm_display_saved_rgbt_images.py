import os
import cv2
import numpy as np
import thermal_image_utils.preprocessing as utils

save_root_dir = 'rgbt_images_for_training'
save_file_prefix = 'rgbt_img'
save_file_interval = 2  # 캡쳐 10번에 1번 저장

# some definition of camera image size
THERMAL_WIDTH = 320
THERMAL_HEIGHT = 256
COLOR_WIDTH = 640
COLOR_HEIGHT = 480

png_list = os.listdir(save_root_dir)

cv2.namedWindow('merged image', cv2.WINDOW_AUTOSIZE)
#cv2.waitKey()

if png_list is not None:
    for (k, file_name) in enumerate(png_list):
        file_with_path = os.path.join(save_root_dir, file_name)
        image = cv2.imread(file_with_path, cv2.IMREAD_UNCHANGED)

        # split image
        rgb_image = image[:COLOR_HEIGHT, :COLOR_WIDTH, :]
        encoded_t_image = image[:THERMAL_HEIGHT, COLOR_WIDTH:, :]
        resized_t_image = utils.crop_boson_320x256_to_320x240(encoded_t_image)

        # thermal image processing
        t_image = utils.decode_thermal_image(resized_t_image)
        #celsius = get_celsius_image(t_image)
        meta = utils.get_default_radiometry_parameters()
        celsius = utils.raw2temp(t_image, meta)
        scaled_celsius = utils.get_scaled_thermal_colormap(celsius, np.min(celsius), np.max(celsius))
        #scaled_celsius = get_scaled_thermal_colormap(celsius, 30, 80)
        resized_scaled_celsius = cv2.resize(scaled_celsius, dsize=(COLOR_WIDTH, COLOR_HEIGHT), interpolation=cv2.INTER_AREA)

        # merge two images
        merged_images = np.hstack((rgb_image, resized_scaled_celsius))

        # Show images
        #cv2.namedWindow('merged image', cv2.WINDOW_AUTOSIZE)
        cv2.imshow('merged image', merged_images)
        cv2.waitKey(100)
        print('file no = ', k, ' / ', len(png_list))


