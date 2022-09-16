import cv2
import numpy as np
import pandas as pd

import os
import sys
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

import thermal_image_utils.preprocessing as utils

save_root_dir = '../rgbt_images_for_training'

# some definition of camera image size
THERMAL_WIDTH = 320
THERMAL_HEIGHT = 256
COLOR_WIDTH = 640
COLOR_HEIGHT = 480

drawing = False
mode = True
ix, iy = -1, -1

def get_zoom_image(input_image, x, y, radius=20, scale=15):
    height = input_image.shape[0]
    width = input_image.shape[1]
    win_size = 2 * radius + 1

    roi_image = np.zeros((2 * radius + 1, 2 * radius + 1, 3), dtype=np.uint8)

    # compute ROI indices w.r.t source image
    src_x_from = max(0, x - radius)
    src_y_from = max(0, y - radius)
    src_x_to = min(width, x + radius + 1)
    src_y_to = min(height, y + radius + 1)

    # compute ROI indices w.r.t. target image
    tgt_x_from = max(0, radius - x)
    tgt_y_from = max(0, radius - y)
    tgt_x_to = min(win_size, win_size + width - (x + radius + 1))
    tgt_y_to = min(win_size, win_size + height - (y + radius + 1))

    roi_image[tgt_y_from:tgt_y_to, tgt_x_from:tgt_x_to, :] = merged_images[src_y_from:src_y_to, src_x_from:src_x_to, :]
    zoomed_roi_image = cv2.resize(roi_image, dsize=(radius * scale + 1, radius * scale + 1), interpolation=cv2.INTER_AREA)

    cv2.line(zoomed_roi_image, (0, radius * scale // 2), (radius * scale, radius * scale // 2), (0, 255, 255), 1)
    cv2.line(zoomed_roi_image, (radius * scale // 2, 0), (radius * scale // 2, radius * scale), (0, 255, 255), 1)
    return zoomed_roi_image

rgb_image_points = []
thermal_image_points = []

def define_correspondences(event,x,y,flags, input_image):
    global ix, iy, drawing, mode
    global rgb_image_points, thermal_image_points

    new_image = input_image.copy()

    if event == cv2.EVENT_LBUTTONDOWN:
        if x > 640:
            thermal_image_points.append((x, y))
            print("thermal image point", (x-640, y), "is appended in thermal-point list")
        else:
            rgb_image_points.append((x, y))
            print("rgb image point", (x, y), "is appended in rgb-point list")


    if event == cv2.EVENT_RBUTTONDOWN:
        if x > 640:
            if len(thermal_image_points) > 0:
                pt = thermal_image_points.pop()
                print("thermal image point", (pt[0]-640, pt[1]), "is removed")
        else:
            if len(rgb_image_points) > 0:
                pt = rgb_image_points.pop()
                print("rgb image point", pt, "is removed")

    zoomed_image = get_zoom_image(input_image, x, y)

    font = cv2.FONT_HERSHEY_DUPLEX
    font_scale = 0.5
    font_thickness = 1
    space_margin = 5

    for k, pt in enumerate(rgb_image_points):
        cv2.circle(new_image, pt, radius=2, color=(0, 0, 255), thickness=-1)
        txt = "%d" % k
        cv2.putText(new_image, txt, (pt[0]+space_margin, pt[1]), font, font_scale, (0, 0, 255), font_thickness)
        if k > 0:
            cv2.line(new_image, rgb_image_points[k-1], rgb_image_points[k], (0,255, 255), 1)
    if len(rgb_image_points) >= 4:
        cv2.line(new_image, rgb_image_points[0], rgb_image_points[-1], (0, 255, 255), 1)


    for k, pt in enumerate(thermal_image_points):
        cv2.circle(new_image, pt, radius=2, color=(0, 255, 0), thickness=-1)
        txt = "%d" % k
        cv2.putText(new_image, txt, (pt[0]+space_margin, pt[1]), font, font_scale, (0, 255, 0), font_thickness)
        if k > 0:
            cv2.line(new_image, thermal_image_points[k-1], thermal_image_points[k], (0, 255, 255), 1)
    if len(thermal_image_points) >= 4:
        cv2.line(new_image, thermal_image_points[0], thermal_image_points[-1], (0, 255, 255), 1)


    cv2.imshow('Zoomed ROI', zoomed_image)
    cv2.imshow('image', new_image)


#merged_images = np.zeros((480,640*2,3), np.uint8)
png_list = os.listdir(save_root_dir)

if png_list is not None:
    file_name = png_list[0]
    file_with_path = os.path.join(save_root_dir, file_name)
    image = cv2.imread(file_with_path, cv2.IMREAD_UNCHANGED)

    # split image
    rgb_image = image[:COLOR_HEIGHT, :COLOR_WIDTH, :]
    encoded_t_image = image[:THERMAL_HEIGHT, COLOR_WIDTH:, :]

    # thermal image processing
    t_image = utils.decode_thermal_image(encoded_t_image)
    #celsius = utils.get_celsius_image(t_image)
    meta = utils.get_default_radiometry_parameters(RTemp=20)
    celsius = utils.raw2temp(t_image, meta)
    scaled_celsius = utils.get_scaled_thermal_colormap(celsius, np.min(celsius), np.max(celsius))
    resized_scaled_celsius = cv2.resize(scaled_celsius, dsize=(640, 480), interpolation=cv2.INTER_AREA)

    # merge two images
    merged_images = np.hstack((rgb_image, resized_scaled_celsius))
    # Show images
    cv2.namedWindow('image', cv2.WINDOW_AUTOSIZE)
    cv2.imshow('image', merged_images)

    cv2.setMouseCallback('image', define_correspondences, merged_images)

    while True:
        k = cv2.waitKey(1) & 0xFF
        if k == ord('c'):
            n_pt_rgb = len(rgb_image_points)
            n_pt_t = len(thermal_image_points)
            if n_pt_rgb == n_pt_t and n_pt_rgb >= 4:
                print('compute homography')

                pts_rgb = np.array(rgb_image_points).reshape(-1, 1, 2).astype(np.float32)
                pts_thermal = np.array(thermal_image_points).reshape(-1, 1, 2).astype(np.float32)
                pts_thermal[:,:,0] = pts_thermal[:,:,0] - 640

                homography, _ = cv2.findHomography(pts_rgb, pts_thermal, cv2.RANSAC)  # pts1과 pts2의 행렬 주의 (N,1,2)
                print(homography)

                gray_image = cv2.cvtColor(rgb_image, cv2.COLOR_BGR2GRAY)
                im_dst = cv2.warpPerspective(rgb_image, homography, (640, 480))

                result = cv2.addWeighted(im_dst, 0.5, resized_scaled_celsius, 0.5, 0.0);

                df = pd.DataFrame(homography)
                writer = pd.ExcelWriter("../homography.xlsx")
                df.to_excel(writer, header=False, index=False)
                writer.close()

                cv2.imshow("result", result)

            else:
                print('Check point correspondences carefully again !!')
        elif k == 27:
            break

cv2.destroyAllWindows()