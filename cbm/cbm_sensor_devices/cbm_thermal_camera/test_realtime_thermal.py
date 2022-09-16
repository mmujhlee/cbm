import os
from thermal_image_utils.preprocessing import *
from cbm_thermal_camera_driver import CbmThermalCameraController
import pandas as pd

# several environment variables for saving as file
image_root_dir = 'rgbt_images_for_training'
save_file_prefix = 'rgbt_img'
thermal_map_file = 'trained_thermal_map.xlsx'

# some definition of camera image size
THERMAL_WIDTH = 320
THERMAL_HEIGHT = 256
COLOR_WIDTH = 640
COLOR_HEIGHT = 480

'''
def measure_temperature(event,x,y,flags, param):
    input_image = param[0]
    thermal_img = param[1]

    font = cv2.FONT_HERSHEY_DUPLEX
    font_scale = 0.5
    font_thickness = 1
    space_margin = 5
    cv2.circle(input_image, (x, y), radius=2, color=(0, 0, 255), thickness=-1)
    txt = "%3.2f" % thermal_img[y,x]
    cv2.putText(input_image, txt, (x + space_margin, y), font, font_scale, (0, 0, 255), font_thickness)
    
    cv2.imshow('blend image', result_image)
'''

def get_overlaied_image(g_image_320x240, celsius_image_320x240, trained_thermal_map):

    # gaussian filtering
    blured_celsius = cv2.GaussianBlur(celsius_image_320x240, (3, 3), cv2.BORDER_DEFAULT)

    current_thermal_map = np.where(blured_celsius > trained_thermal_map + trained_thermal_map * 0.01, blured_celsius,0)
    scaled_thermal_map = get_scaled_thermal_colormap(current_thermal_map, 0, 60)

    mask_thermal = np.where(current_thermal_map > 0, 1.0, 0.0)
    mask_background = 1 - mask_thermal

    gray_image = cv2.cvtColor(g_image_320x240, cv2.COLOR_GRAY2BGR)

    result_image = cv2.addWeighted(gray_image, 0.4, scaled_thermal_map, 0.6, 0.0)

    mask_background = mask_background.reshape(*mask_background.shape, 1)
    background = (mask_background * gray_image).astype(np.uint8)

    mask_thermal = mask_thermal.reshape(*mask_thermal.shape, 1)
    result_image = (result_image * mask_thermal).astype(np.uint8)

    result_image = cv2.bitwise_or(background, result_image)
    return result_image


trained_thermal_map = pd.read_excel(thermal_map_file, header=None).to_numpy()

homography = pd.read_excel('homography.xlsx', header=None).to_numpy()

controller_handle = CbmThermalCameraController('image')
controller_handle.start()
#meta = utils.get_default_radiometry_parameters(RTemp=20)
#homography = pd.read_excel('homography.xlsx', header=None).to_numpy()

try:
    while True:
        frame = controller_handle.get_recent_data(is_one_encoded_image=True)
        if frame is not None:
            gray_img, celsius_img = controller_handle.decode_rgbt_image(frame)
            colorized_img = get_scaled_thermal_colormap(celsius_img, min_temp=np.min(celsius_img),max_temp=np.max(celsius_img))
            overay = get_overlaied_image(gray_img, celsius_img, trained_thermal_map)

            cv2.imshow('encoded image', frame)
            cv2.imshow('decoded gray_image', gray_img)
            cv2.imshow('decoded thermal image', colorized_img)
            cv2.imshow('overay', overay)
            cv2.waitKey(10)
finally:
    controller_handle.stop()


