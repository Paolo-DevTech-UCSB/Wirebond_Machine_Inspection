from preprocess.ToDo_Manager import print_module_summary, save_checked_entry, load_checked_list, extract_raw_prefix, find_raw_image, ensure_folder, log_move, print_module_summary, init_module_summary
from PIL import Image
import os
import preprocess.Image_Processing_Tools as IPT
import shutil
import preprocess.SetQuality_Checker as SetQuality_Checker
import matplotlib.pyplot as plt
import numpy as np
from Folder_to_Report_config import CONFIG
from preprocess.Folder_Builder import get_module_paths

import re

def crop_around_center(img, cx, cy, size=600):
    W, H = img.size
    half = size // 2

    left = int(cx - half)
    top  = int(cy - half)

    # Clamp to image bounds
    left = max(0, min(left, W - size))
    top  = max(0, min(top, H - size))

    return IPT.Img_Crop(img, left, top, size, size)

def validate_crop(crop_img):
    return True
    #return detect_sensor_with_fr4_ring(crop_img)

def compute_sensor_com(raw_img):
    W, H = raw_img.size
    pixels = raw_img.load()

    xs = []
    ys = []

    for y in range(H):
        for x in range(W):
            r, g, b = pixels[x, y]
            if is_sensor_color(r, g, b):
                xs.append(x)
                ys.append(y)

    if len(xs) == 0:
        return None, None

    return np.mean(xs), np.mean(ys)

def compute_gold_com(raw_img):
    W, H = raw_img.size
    pixels = raw_img.load()

    xs = []
    ys = []

    for y in range(H):
        for x in range(W):
            r, g, b = pixels[x, y]
            # gold pads = high R, medium G, low B
            if r > 180 and g > 120 and b < 100:
                xs.append(x)
                ys.append(y)

    if len(xs) == 0:
        return None, None

    return np.mean(xs), np.mean(ys)

def recover_center(raw_img):
    # 1. Mercedes spokes
    try:
        cx, cy = center_default(raw_img)
        if cx is not None and cy is not None:
            crop = crop_around_center(raw_img, cx, cy)
            if validate_crop(crop):
                return cx, cy, crop
    except:
        pass

    # 2. Sensor COM
    cx, cy = compute_sensor_com(raw_img)
    if cx is not None and cy is not None:
        crop = crop_around_center(raw_img, cx, cy)
        if validate_crop(crop):
            return cx, cy, crop

    # 3. Gold COM
    cx, cy = compute_gold_com(raw_img)
    if cx is not None and cy is not None:
        crop = crop_around_center(raw_img, cx, cy)
        if validate_crop(crop):
            return cx, cy, crop

    # 4. Weighted peak center
    results = SetQuality_Checker.debug_integral_bands(raw_img)
    cx, cy = results["weighted_peak_center"]
    if cx is not None and cy is not None:
        crop = crop_around_center(raw_img, cx, cy)
        if validate_crop(crop):
            return cx, cy, crop

    # All failed
    return None, None, None








def extract_raw_prefix(processed_filename):
    base = os.path.splitext(processed_filename)[0]
    base = base.replace("_processed", "")
    parts = base.split("_")

    # Collect numeric parts only
    numeric = [p for p in parts if p.isdigit()]

    # Require exactly 3 trailing numeric parts
    if len(numeric) < 3:
        return None

    prefix = "_".join(numeric[-3:])

    # Reject invalid prefixes like 0_0_0
    if prefix == "0_0_0":
        return None

    return prefix

def find_raw_image(module, raw_prefix, RAW_DIR):
    module_dir = os.path.join(RAW_DIR, module)
    if not os.path.exists(module_dir):
        return None

    files = sorted(os.listdir(module_dir))

    # Prefer exact match
    exact = raw_prefix + ".png"
    if exact in files:
        return os.path.join(module_dir, exact)

    # Otherwise prefix match
    for f in files:
        if f.startswith(raw_prefix):
            return os.path.join(module_dir, f)

    return None

def Post_Default_Cleanup():

    base = CONFIG["BASE_DIR"]
    input_root = os.path.join(base, CONFIG["INPUT_DIR"])
    processed_root = os.path.join(base, CONFIG["PROCESSED_DIR"])

    CATEGORY_FOLDERS = set(CONFIG["MODULE_OUTPUT_FOLDERS"])

    modules = [
        d for d in os.listdir(processed_root)
        if os.path.isdir(os.path.join(processed_root, d))
        and d not in CATEGORY_FOLDERS
    ]
    for module in modules:

        print(f"\n=== Checking module: {module} ===")

        module_input, module_output = get_module_paths(module)
        DEFAULT_DIR = module_output["Default"]
        UNPROCESSED_DIR = module_output["Unprocessed"]

        TODOS_DIR = os.path.join(processed_root, module, "ToDos")
        ensure_folder(TODOS_DIR)

        default_images = [
            f for f in os.listdir(DEFAULT_DIR)
            if f.lower().endswith(".png")
        ]

        print(f"Found {len(default_images)} Default images to check.")

        summary = init_module_summary()

        for filename in default_images:

            summary["checked"] += 1
            img_path = os.path.join(DEFAULT_DIR, filename)

            checked = load_checked_list(TODOS_DIR)
            if filename in checked:
                continue

            try:
                img = Image.open(img_path)
                img.load()
            except:
                print("Could not open:", img_path)
                save_checked_entry(TODOS_DIR, filename)
                continue

            # Validate existing crop
            if validate_crop(img):
                summary["ok"] += 1
                print(f"[OK] {filename}")
                save_checked_entry(TODOS_DIR, filename)
                continue

            # BAD → try to fix
            print(f"[BAD] {filename}")
            summary["bad"] += 1

            debug_sensor_fr4_ring(img)


            raw_prefix = extract_raw_prefix(filename)
            if raw_prefix is None:
                summary["raw_missing"] += 1
                print("Could not extract RAW prefix:", filename)
                save_checked_entry(TODOS_DIR, filename)
                continue

            raw_path = find_raw_image(module, raw_prefix, input_root)
            if raw_path is None:
                summary["raw_missing"] += 1
                print("RAW image not found for:", raw_prefix)
                save_checked_entry(TODOS_DIR, filename)
                continue

            raw_img = IPT.Load_Img(raw_path)
            if raw_img is None:
                summary["raw_missing"] += 1
                print("RAW image unreadable:", raw_path)
                save_checked_entry(TODOS_DIR, filename)
                continue

            # Try multi-stage center recovery
            cx, cy, fixed_crop = recover_center(raw_img)

            if fixed_crop is not None:
                # Save corrected crop
                save_path = os.path.join(DEFAULT_DIR, filename)
                fixed_crop.save(save_path)
                summary["fixed"] += 1
                print(f"[FIXED] {filename}")
                save_checked_entry(TODOS_DIR, filename)
                continue

            # All recovery attempts failed
            summary["center_fail"] += 1
            print(f"[UNFIXABLE] {filename}")
            save_checked_entry(TODOS_DIR, filename)



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
#    plt.show()

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
