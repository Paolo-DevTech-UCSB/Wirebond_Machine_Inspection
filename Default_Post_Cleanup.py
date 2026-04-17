from wb_config import RAW_DIR, PROCESSED_DIR
from PIL import Image
import os
import Image_Processing_Tools as IPT
import shutil
import SetQuality_Checker
import matplotlib.pyplot as plt
import numpy as np

import re


def extract_raw_prefix(processed_filename):
    """
    Extracts the RAW coordinate tail from a processed filename.
    Example:
        320MHF2TDSB0091_118_119_138_processed.png → "118_119_138"
    """

    base = os.path.splitext(processed_filename)[0]
    base = base.replace("_processed", "")

    # Split by underscores
    parts = base.split("_")

    # RAW coords are ALWAYS the last 3 numeric parts
    raw_parts = []

    # Walk backwards and collect numeric parts
    for p in reversed(parts):
        if p.isdigit():
            raw_parts.append(p)
            if len(raw_parts) == 3:
                break
        else:
            break

    if len(raw_parts) == 0:
        return None

    # Reverse back to correct order
    raw_parts.reverse()

    return "_".join(raw_parts)


def find_raw_image(module, raw_prefix, RAW_DIR):
    """
    Finds any RAW file in the module folder that starts with the extracted prefix.
    """
    module_dir = os.path.join(RAW_DIR, module)

    if not os.path.exists(module_dir):
        return None

    for f in os.listdir(module_dir):
        if f.startswith(raw_prefix):
            return os.path.join(module_dir, f)

    return None


def Post_Default_Cleanup():

    default_dir = os.path.join(PROCESSED_DIR, "Default")

    if not os.path.exists(default_dir):
        print("No Default folder found in PROCESSED_DIR")
        return

    default_images = [
        os.path.join(default_dir, f)
        for f in os.listdir(default_dir)
        if f.lower().endswith(".png")
    ]

    print(f"Found {len(default_images)} Default images to check.")

    for img_path in default_images:

        try:
            img = Image.open(img_path)
        except:
            print("Could not open:", img_path)
            continue

        ok = detect_sensor_with_fr4_ring(img)

        if ok:
            print(f"[OK] Sensor + FR4 ring detected → {img_path}")
            continue

        # ---------------------------------------------------------
        # BAD IMAGE → REPROCESS
        # ---------------------------------------------------------
        print(f"[BAD] Missing sensor or FR4 ring → {img_path}")

        filename = os.path.basename(img_path)

        # Extract module name (everything before first underscore)
        module = filename.split("_")[0]

        # Extract RAW prefix from processed filename
        raw_prefix = extract_raw_prefix(filename)

        if raw_prefix is None:
            print("Could not extract RAW prefix from:", filename)
            continue

        # Find the RAW file
        raw_path = find_raw_image(module, raw_prefix, RAW_DIR)

        if raw_path is None:
            print("RAW image not found:", os.path.join(RAW_DIR, module, raw_prefix + "*.png"))
            continue

        raw_img = IPT.Load_Img(RAW_DIR, module, os.path.basename(raw_path))

        # ---------------------------------------------------------
        # 2. Re-run SetQuality Checker to get NEW center
        # ---------------------------------------------------------
        results = SetQuality_Checker.debug_integral_bands(raw_img)
        new_cx, new_cy = results["weighted_peak_center"]

        if new_cx is None or new_cy is None:
            print("Could not compute new center. Skipping.")
            continue

        # ---------------------------------------------------------
        # 3. Build a NEW classification crop
        # ---------------------------------------------------------
        Left = new_cx - 300
        Top  = new_cy - 300

        new_crop = IPT.Img_Crop(raw_img, Left, Top, 600, 600)

        # ---------------------------------------------------------
        # 4. Re-classify the image
        # ---------------------------------------------------------
        new_class = IPT.Classify_Img(new_crop, 0, 0)

        print(f"Reclassified as: {new_class}")

        # ---------------------------------------------------------
        # 5. If class changed → move file to correct folder
        # ---------------------------------------------------------
        if new_class != "Default":
            new_folder = os.path.join(PROCESSED_DIR, new_class)
            os.makedirs(new_folder, exist_ok=True)

            new_path = os.path.join(new_folder, filename)

            print(f"Moving {filename} → {new_class}")
            shutil.move(img_path, new_path)

        else:
            print("Still Default after reprocessing. Leaving in place.")




def debug_sensor_fr4_ring(img):
    """
    Visual debugger for the sensor circle + FR4 ring detector.
    Shows:
      - Sensor hit ratio
      - FR4 hit ratio
      - Visual overlay of ring regions
    """

    W, H = img.size
    cx, cy = W // 2, H // 2
    pixels = img.load()

    SENSOR_RADIUS = 175
    SENSOR_TOL    = 20

    # -----------------------------------------
    # NEW: inner edge moved inward by 100 px
    # -----------------------------------------
    SENSOR_INNER = SENSOR_RADIUS - (SENSOR_TOL + 100)
    SENSOR_OUTER = SENSOR_RADIUS + SENSOR_TOL

    FR4_INNER = SENSOR_OUTER + 10
    FR4_OUTER = SENSOR_OUTER + 60

    sensor_count = 0
    sensor_total = 0

    fr4_count = 0
    fr4_total = 0

    # Visualization buffer
    vis = np.zeros((H, W, 3), dtype=np.uint8)

    for y in range(H):
        for x in range(W):
            r, g, b = pixels[x, y]
            R = ((x - cx)**2 + (y - cy)**2)**0.5

            # SENSOR BAND (now wider inward)
            if SENSOR_INNER <= R <= SENSOR_OUTER:
                sensor_total += 1
                if is_sensor_color(r, g, b):
                    sensor_count += 1
                    vis[y, x] = [0, 255, 0]   # green = sensor hit
                else:
                    vis[y, x] = [255, 0, 0]   # red = sensor miss

            # FR4 BAND
            elif FR4_INNER <= R <= FR4_OUTER:
                fr4_total += 1
                if is_FR4_color(r, g, b):
                    fr4_count += 1
                    vis[y, x] = [0, 0, 255]   # blue = FR4 hit
                else:
                    vis[y, x] = [255, 255, 0] # yellow = FR4 miss

            # Outside debug region
            else:
                vis[y, x] = [
                    pixels[x, y][0] // 2,
                    pixels[x, y][1] // 2,
                    pixels[x, y][2] // 2
                ]

    # Avoid divide-by-zero
    sensor_ratio = sensor_count / sensor_total if sensor_total else 0
    fr4_ratio    = fr4_count / fr4_total if fr4_total else 0

    print("\n==============================")
    print(" SENSOR + FR4 RING DEBUGGER")
    print("==============================")
    print(f"Sensor hits: {sensor_count}/{sensor_total}  → {sensor_ratio:.3f}")
    print(f"FR4 hits:    {fr4_count}/{fr4_total}      → {fr4_ratio:.3f}")
    print("==============================\n")

    # Show visualization
    plt.figure(figsize=(6, 6))
    plt.imshow(vis)
    plt.title(f"Sensor={sensor_ratio:.2f},  FR4={fr4_ratio:.2f}")
    plt.axis("off")
    plt.show()

    return sensor_ratio, fr4_ratio


def is_sensor_color(r, g, b):
    return (
        70 <= r <= 190 and     # widened for new high-R samples
        140 <= g <= 240 and    # widened for new high-G samples
        180 <= b <= 255 and    # widened for new high-B samples
        b > g > r              # preserve the strong channel ordering
    )

def is_FR4_color(r, g, b):
    # FR4 ranges from dark olive to bright green
    return (
        70 <= r <= 200 and     # covers dark → bright FR4
        110 <= g <= 255 and    # green always dominant
        50 <= b <= 180 and     # blue mid-range
        g > r and              # green highest
        g > b                  # green highest
    )



def detect_sensor_with_fr4_ring(img):
    """
    1. Checks for a SENSOR-colored circular band in the center.
    2. Checks for an FR4 ring surrounding it.
    Returns True if both conditions are satisfied.
    """

    W, H = img.size
    cx, cy = W // 2, H // 2
    pixels = img.load()

    SENSOR_RADIUS = 175          # center radius stays the same
    SENSOR_TOL    = 20           # outer tolerance stays the same

    # -----------------------------------------
    # NEW: inner edge moved inward by 100 px
    # -----------------------------------------
    SENSOR_INNER = SENSOR_RADIUS - (SENSOR_TOL + 100)
    SENSOR_OUTER = SENSOR_RADIUS + SENSOR_TOL

    FR4_INNER = SENSOR_OUTER + 10
    FR4_OUTER = SENSOR_OUTER + 60

    sensor_count = 0
    sensor_total = 0

    fr4_count = 0
    fr4_total = 0

    for y in range(H):
        for x in range(W):
            r, g, b = pixels[x, y]
            R = ((x - cx)**2 + (y - cy)**2)**0.5

            # --- SENSOR BAND CHECK (now wider inward) ---
            if SENSOR_INNER <= R <= SENSOR_OUTER:
                sensor_total += 1
                if is_sensor_color(r, g, b):
                    sensor_count += 1

            # --- FR4 RING CHECK ---
            if FR4_INNER <= R <= FR4_OUTER:
                fr4_total += 1
                if is_FR4_color(r, g, b):
                    fr4_count += 1

    # Avoid division by zero
    if sensor_total == 0 or fr4_total == 0:
        return False

    sensor_ratio = sensor_count / sensor_total
    fr4_ratio    = fr4_count / fr4_total

    SENSOR_OK = sensor_ratio > 0.30
    FR4_OK    = fr4_ratio > 0.30

    return SENSOR_OK and FR4_OK
