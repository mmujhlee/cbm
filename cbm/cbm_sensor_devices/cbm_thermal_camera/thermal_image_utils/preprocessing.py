import numpy as np
import cv2
import math
'''
def encode_rgbt_image(rgb_image_640x480, thermal_image_320x256):
    t_img = crop_boson_320x256_to_320x240(thermal_image_320x256)
    g_img = cv2.cvtColor(rgb_image_640x480, cv2.COLOR_BGR2GRAY)

    warp_image = cv2.warpPerspective(g_img, self.homography, (640, 480))
    g_img = cv2.resize(warp_image, (320, 240), interpolation=cv2.INTER_CUBIC)

    encoded_image = encode_thermal_image(t_img)
    encoded_image[:, :, 2] = g_img
    return encoded_image
'''

def decode_rgbt_image(encoded_image):
    gray_image = encoded_image[:, :, 2]
    decoded_t = decode_thermal_image(encoded_image)
    meta = get_default_radiometry_parameters(RTemp=20)
    celsius_image = raw2temp(decoded_t, meta)
    return gray_image, celsius_image

def encode_thermal_image(thermal_image):
    thermal_high_byte = ((thermal_image & 0xff00) >> 8).astype(np.uint8)
    thermal_low_byte = (thermal_image & 0x00ff).astype(np.uint8)
    height, width = thermal_image.shape
    merged_image = np.zeros((height, width, 3), dtype=np.uint8)
    merged_image[:, :, 0] = thermal_high_byte
    merged_image[:, :, 1] = thermal_low_byte
    return merged_image

def decode_thermal_image(encoded_image):
    high = encoded_image[:, :, 0]
    low = encoded_image[:, :, 1]
    decoded_image = ((high.astype(np.uint16) << 8) & 0xff00) | (low.astype(np.uint16) & 0x00ff)
    return decoded_image

def get_celsius_image(thermal_image):
    #img_celsius = thermal_image.astype(np.float32) / 100.0 - 273.15
    img_celsius = thermal_image.astype(np.float32) / 1000.0
    return img_celsius

def get_scaled_thermal_colormap(celsius_image, min_temp=0, max_temp=100):
    tmp_img = np.where(celsius_image > max_temp, max_temp, celsius_image)
    tmp_img = np.where(tmp_img < min_temp, min_temp, tmp_img)
    img_thermal = 255 * (tmp_img - min_temp) / (max_temp - min_temp)
    #img_col = cv2.applyColorMap(img_thermal.astype(np.uint8), cv2.COLORMAP_INFERNO)
    img_col = cv2.applyColorMap(img_thermal.astype(np.uint8), cv2.COLORMAP_HOT)
    return img_col

def crop_boson_320x256_to_320x240(img):
    if len(img.shape) == 2:
        (h, w) = img.shape
    else:
        (h, w, _) = img.shape

    start_idx = int((h - 240)/2)
    end_idx = start_idx + 240
    return img[start_idx:end_idx, :]


def get_default_radiometry_parameters(RTemp=20):
    # RTemp = 10  # 방사 온도 = 대기온도 = 윈도우 온도로 가정
    meta = {}

    meta["Atmospheric Trans Alpha 1"] = 0.006569
    meta["Atmospheric Trans Alpha 2"] = 0.01262
    meta["Atmospheric Trans Beta 1"] = -0.002276
    meta["Atmospheric Trans Beta 2"] = -0.00667
    meta["Atmospheric Trans X"] = 1.9
    meta["Planck R1"] = 14906.216
    meta["Planck R2"] = 0.010956882
    meta["Planck O"] = -7261
    meta["Planck B"] = 1396.5
    meta["Planck F"] = 1
    meta["Emissivity"] = 1
    meta["IR Window Transmission"] = 1
    meta["IR Window Temperature"] = RTemp  # 실측치 <- 대기온도
    meta["Object Distance"] = 1
    meta["Atmospheric Temperature"] = RTemp
    meta["Reflected Apparent Temperature"] = RTemp
    meta["Relative Humidity"] = 50  # 상대습도
    return meta

def raw2temp(raw, meta):
    """
    Convert raw pixel values to temperature, if calibration coefficients are known. The
    equations for atmospheric and window transmission are found in Minkina and Dudzik, as
    well as some of FLIR's documentation.

    Roughly ported from ThermImage: https://github.com/gtatters/Thermimage/blob/master/R/raw2temp.R

    """

    ATA1 = float(meta["Atmospheric Trans Alpha 1"])
    ATA2 = float(meta["Atmospheric Trans Alpha 2"])
    ATB1 = float(meta["Atmospheric Trans Beta 1"])
    ATB2 = float(meta["Atmospheric Trans Beta 2"])
    ATX = float(meta["Atmospheric Trans X"])
    PR1 = float(meta["Planck R1"])
    PR2 = float(meta["Planck R2"])
    PO = float(meta["Planck O"])
    PB = float(meta["Planck B"])
    PF = float(meta["Planck F"])
    E = float(meta["Emissivity"])
    IRT = float(meta["IR Window Transmission"])
    IRWTemp = meta["IR Window Temperature"]
    OD = meta["Object Distance"]
    ATemp = meta["Atmospheric Temperature"]
    RTemp = meta["Reflected Apparent Temperature"]
    humidity = meta["Relative Humidity"]

    # Equations to convert to temperature
    # See http://130.15.24.88/exiftool/forum/index.php/topic,4898.60.html
    # Standard equation: temperature<-PB/log(PR1/(PR2*(raw+PO))+PF)-273.15
    # Other source of information: Minkina and Dudzik's Infrared Thermography: Errors and Uncertainties

    window_emissivity = 1 - IRT
    window_reflectivity = 0

    # Converts relative humidity into water vapour pressure (mmHg)
    water = (humidity/100.0)*math.exp(1.5587+0.06939*(ATemp)-0.00027816*(ATemp)**2+0.00000068455*(ATemp)**3)

    #tau1 = ATX*np.exp(-np.sqrt(OD/2))
    tau1 = ATX*np.exp(-np.sqrt(OD/2)*(ATA1+ATB1*np.sqrt(water)))+(1-ATX)*np.exp(-np.sqrt(OD/2)*(ATA2+ATB2*np.sqrt(water)))
    tau2 = tau1

    # transmission through atmosphere - equations from Minkina and Dudzik's Infrared Thermography Book
    # Note: for this script, we assume the thermal window is at the mid-point (OD/2) between the source
    # and the camera sensor

    raw_refl = PR1/(PR2*(np.exp(PB/(RTemp+273.15))-PF))-PO   # radiance reflecting off the object before the window
    raw_refl_attn = (1-E)/E*raw_refl   # attn = the attenuated radiance (in raw units)

    raw_atm1 = PR1/(PR2*(np.exp(PB/(ATemp+273.15))-PF))-PO # radiance from the atmosphere (before the window)
    raw_atm1_attn = (1-tau1)/E/tau1*raw_atm1 # attn = the attenuated radiance (in raw units)

    raw_window = PR1/(PR2*(np.exp(PB/(IRWTemp+273.15))-PF))-PO
    einv = 1./E/tau1/IRT
    raw_window_attn = window_emissivity*einv*raw_window

    raw_refl2 = raw_refl
    raw_refl2_attn = window_reflectivity*einv*raw_refl2

    raw_atm2 = raw_atm1
    ediv = einv/tau2
    raw_atm2_attn = (1-tau2)*ediv*raw_atm2

    # These last steps are pretty slow and
    # could probably be sped up a lot
    raw_sub = -raw_atm1_attn-raw_atm2_attn-raw_window_attn-raw_refl_attn-raw_refl2_attn
    raw_object = np.add(np.multiply(raw, ediv), raw_sub)

    raw_object = np.add(raw_object, PO)
    raw_object = np.multiply(raw_object, PR2)
    raw_object_inv = np.multiply(np.reciprocal(raw_object), PR1)
    raw_object_inv = np.add(raw_object_inv, PF)
    raw_object_log = np.log(raw_object_inv)
    temp = np.multiply(np.reciprocal(raw_object_log), PB)

    return temp - 273.15

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