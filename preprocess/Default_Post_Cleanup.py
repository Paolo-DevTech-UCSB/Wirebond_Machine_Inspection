from preprocess.ToDo_Manager import print_module_summary, save_checked_entry, load_checked_list, extract_raw_prefix, find_raw_image, ensure_folder, log_move, print_module_summary, init_module_summary
from wb_config import RAW_DIR, PROCESSED_DIR
from PIL import Image
import os
import preprocess.Image_Processing_Tools as IPT
import shutil
import preprocess.SetQuality_Checker as SetQuality_Checker
import matplotlib.pyplot as plt
import numpy as np

import re

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

    DEFAULT_DIR = os.path.join(PROCESSED_DIR, "Default")
    #UNPROCESSED_DIR = os.path.join(PROCESSED_DIR, "Unprocessed")
    UNPROCESSED_DIR = os.path.join(PROCESSED_DIR, "Unprocessed")

    TODOS_DIR = os.path.join(PROCESSED_DIR, "ToDos")

    ensure_folder(UNPROCESSED_DIR)
    ensure_folder(TODOS_DIR)

    if not os.path.exists(DEFAULT_DIR):
        print("No Default folder found.")
        return

    default_images = [
        f for f in os.listdir(DEFAULT_DIR)
        if f.lower().endswith(".png")
    ]

    print(f"Found {len(default_images)} Default images to check.")

    #log
    current_module = None
    summary = None



    for filename in default_images:
        module = filename.split("_")[0]


        # --------------------------------------------
        # Detect module change and print previous summary
        # --------------------------------------------
        if module != current_module:
            if summary is not None:
                print_module_summary(current_module, summary)

            summary = init_module_summary()
            current_module = module


        summary["checked"] += 1

        img_path = os.path.join(DEFAULT_DIR, filename)

        # --------------------------------------------
        # Determine module name (everything before first "_")
        # --------------------------------------------
        module = filename.split("_")[0]

        # --------------------------------------------
        # Load per-module checked list
        # --------------------------------------------
        module_todo_dir = os.path.join(TODOS_DIR, module)
        ensure_folder(module_todo_dir)

        checked = load_checked_list(module_todo_dir)

        # Skip if already processed
        if filename in checked:
            continue

        # --------------------------------------------
        # Try to open the processed image
        # --------------------------------------------
        try:
            img = Image.open(img_path)
        except:
            print("Could not open:", img_path)
            save_checked_entry(module_todo_dir, filename)
            continue

        # --------------------------------------------
        # Run sensor + FR4 ring detection
        # --------------------------------------------
        ok = detect_sensor_with_fr4_ring(img)

        if ok:
            summary["ok"] += 1        # ← ADD THIS
            print(f"[OK] Sensor + FR4 ring detected → {filename}")
            save_checked_entry(module_todo_dir, filename)
            continue

        # --------------------------------------------
        # BAD IMAGE → REPROCESS
        # --------------------------------------------
        print(f"[BAD] Missing sensor or FR4 ring → {filename}")
        summary["bad"] += 1           # ← ADD THIS

        # Extract RAW prefix
        raw_prefix = extract_raw_prefix(filename)
        if raw_prefix is None:
            summary["raw_missing"] += 1   # ← ADD THIS
            print("Could not extract RAW prefix:", filename)
            save_checked_entry(module_todo_dir, filename)
            continue

        # Find RAW image
        raw_path = find_raw_image(module, raw_prefix, RAW_DIR)
        if raw_path is None:
            summary["raw_missing"] += 1   # ← ADD THIS
            print("RAW image not found for:", raw_prefix)
            save_checked_entry(module_todo_dir, filename)
            continue

        # Load RAW image
        raw_img = IPT.Load_Img(RAW_DIR, module, os.path.basename(raw_path))

        # --------------------------------------------
        # Compute NEW center using SetQuality Checker
        # --------------------------------------------
        results = SetQuality_Checker.debug_integral_bands(raw_img)
        new_cx, new_cy = results["weighted_peak_center"]

        if new_cx is None or new_cy is None:
            summary["center_fail"] += 1   # ← ADD THIS
            print("Could not compute new center. Moving to Unprocessed.")
            dst = os.path.join(UNPROCESSED_DIR, filename)
            shutil.move(img_path, dst)
            log_move(img_path, dst)
            save_checked_entry(module_todo_dir, filename)
            continue

        # --------------------------------------------
        # Build NEW crop around new center
        # --------------------------------------------
        Left = new_cx - 300
        Top  = new_cy - 300
        new_crop = IPT.Img_Crop(raw_img, Left, Top, 600, 600)

        # --------------------------------------------
        # Re-classify the new crop
        # --------------------------------------------
        new_class = IPT.Classify_Img(new_crop, 0, 0)
        print(f"Reclassified as: {new_class}")

        # --------------------------------------------
        # Move file based on new classification
        # --------------------------------------------
        if new_class != "Default":
            # Move to correct classified folder
            summary["reclassified"] += 1
            new_folder = os.path.join(PROCESSED_DIR, new_class)
        else:
            summary["moved_unprocessed"] += 1   # ← ADD THIS
            # Move to Unprocessed instead of leaving in Default
            new_folder = UNPROCESSED_DIR

        ensure_folder(new_folder)
        dst = os.path.join(new_folder, filename)

        shutil.move(img_path, dst)
        log_move(img_path, dst)

        # --------------------------------------------
        # Mark as checked
        # --------------------------------------------
        save_checked_entry(module_todo_dir, filename)

    if summary is not None:
        print_module_summary(current_module, summary)




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
