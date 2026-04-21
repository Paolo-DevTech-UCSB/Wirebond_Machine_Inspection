# orientation_verifier.py

import cv2
import numpy as np
from PIL import Image

import os

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
MASK_PATH = os.path.join(CURRENT_DIR, "WideMercMask2.png")

MERC_MASK = cv2.imread(MASK_PATH, cv2.IMREAD_GRAYSCALE)

MERC_MASK = cv2.resize(MERC_MASK, (200, 200))

def extract_mercedes_region(processed_img):
    arr = np.array(processed_img)
    gray = cv2.cvtColor(arr, cv2.COLOR_BGR2GRAY)
    cx, cy, r = 300, 300, 100
    return gray[cy-r:cy+r, cx-r:cx+r]

def mercedes_correlation(crop):
    crop_resized = cv2.resize(crop, MERC_MASK.shape[::-1])
    result = cv2.matchTemplate(crop_resized, MERC_MASK, cv2.TM_CCOEFF_NORMED)
    return float(result[0][0])

def verify_orientation(processed_img):
    crop = extract_mercedes_region(processed_img)
    score = mercedes_correlation(crop)
    return score
