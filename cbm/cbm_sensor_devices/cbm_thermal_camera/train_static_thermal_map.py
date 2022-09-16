import os
from thermal_image_utils.preprocessing import *
import pandas as pd

# several environment variables for saving as file
#save_root_dir = './image/'
#save_root_dir = 'E:/raw_data/research/2021_CBM_rgbt_images/test_images'
save_root_dir = 'rgbt_images_for_training'
save_file_prefix = 'rgbt_img'
save_file_interval = 2  # 캡쳐 10번에 1번 저장

# some definition of camera image size
THERMAL_WIDTH = 320
THERMAL_HEIGHT = 256
COLOR_WIDTH = 640
COLOR_HEIGHT = 480

thermal_map = np.zeros((240, 320), dtype=np.float32)

png_list = os.listdir(save_root_dir)


cv2.namedWindow('merged image', cv2.WINDOW_AUTOSIZE)
cv2.namedWindow('thermal_map', cv2.WINDOW_AUTOSIZE)

cv2.waitKey()

if png_list is not None:
    for (k, file_name) in enumerate(png_list):
        file_with_path = os.path.join(save_root_dir, file_name)
        image = cv2.imread(file_with_path, cv2.IMREAD_UNCHANGED)

        # split image
        rgb_image = image[:COLOR_HEIGHT, :COLOR_WIDTH, :]
        encoded_t_image = image[:THERMAL_HEIGHT, COLOR_WIDTH:, :]

        # thermal image processing
        t_image = decode_thermal_image(encoded_t_image)
        #celsius = get_celsius_image(t_image)
        celsius = raw2temp(t_image, get_default_radiometry_parameters(RTemp=20))

        # update thermal map
        resized_celsius = crop_boson_320x256_to_320x240(celsius)
        #resized_celsius = cv2.resize(celsius, dsize=(640, 480), interpolation=cv2.INTER_AREA)

        # gaussian filtering
        resized_celsius = cv2.GaussianBlur(resized_celsius, (3, 3), cv2.BORDER_DEFAULT)

        thermal_map = np.where(resized_celsius > thermal_map, resized_celsius, thermal_map)
        scaled_thermal_map = get_scaled_thermal_colormap(thermal_map, np.min(thermal_map), np.max(thermal_map))
        #print(scaled_thermal_map[1, :5])

        # scaling of current thermal image
        scaled_celsius = get_scaled_thermal_colormap(celsius, np.min(celsius), np.max(celsius))
        resized_scaled_celsius = cv2.resize(scaled_celsius, dsize=(640, 480), interpolation=cv2.INTER_AREA)

        # merge two images
        merged_images = np.hstack((rgb_image, resized_scaled_celsius))

        # Show images
        #cv2.namedWindow('thermal_map', cv2.WINDOW_AUTOSIZE)
        cv2.imshow('thermal_map', scaled_thermal_map)

        #cv2.namedWindow('merged image', cv2.WINDOW_AUTOSIZE)
        cv2.imshow('merged image', merged_images)

        cv2.waitKey(1)
        print('file no = ', k, ' / ', len(png_list))

cv2.waitKey()

df = pd.DataFrame(thermal_map)
#file_with_path = os.path.join(save_root_dir, 'trained_thermal_map.xlsx')
writer = pd.ExcelWriter("trained_thermal_map.xlsx")
df.to_excel(writer, header=False, index=False)
writer.close()