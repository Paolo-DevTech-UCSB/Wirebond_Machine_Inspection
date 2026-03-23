from PIL import Image
import os
import Inital_Image_Processor_DSKTP as IIP
from wb_config import RAW_DIR, PROCESSED_DIR

def Main(Current_Module, Image_Name):

    # Load raw image
    img_path = os.path.join(RAW_DIR, Current_Module, Image_Name)
    try:
        img = Image.open(img_path)
        img.load()
    except Exception as e:
        print(f"[SKIP] Cannot open image {img_path}: {e}")
        return None

    # Get offsets + flip flag
    result = IIP.Main(Current_Module, Image_Name)

    # If IIP failed, skip this image
    if result == (None, None, None, "Default"):
        print(f"[SKIP] Could not process {Image_Name} in {Current_Module}")
        return None

    if not isinstance(result, (list, tuple)) or len(result) != 4:
        print("ERROR — Unexpected IIP return format:", result)
    PCBX, PCBY, more_above, Hole_Type = result

    # Crop
    X_BIAS = 0
    left   = PCBX - 500 + X_BIAS
    top    = PCBY - 412
    right  = PCBX + 500 + X_BIAS
    bottom = PCBY + 412

    # Compute crop center
    crop_center_x = (left + right) / 2
    crop_center_y = (top + bottom) / 2

    # Compare to PCB center
    dx = crop_center_x - PCBX
    dy = crop_center_y - PCBY

    TOL = 5  # pixels

    #print(f"Crop center: ({crop_center_x:.1f}, {crop_center_y:.1f})")
    #print(f"PCB center:  ({PCBX}, {PCBY})")
    #print(f"Offset:      dx={dx:.1f}, dy={dy:.1f})")

    #if abs(dx) > TOL or abs(dy) > TOL:
    #    print('⚠️ WARNING: Crop is not centered on PCB beyond tolerance.')
    #else:
    #    print('✅ Crop is centered within tolerance.')

    cropped_img = img.crop((left, top, right, bottom))
    #cropped_img = img.crop((400 + PCBX, 375 + PCBY, 1400 + PCBX, 1200 + PCBY))

    # Flip if needed
    if more_above:
        flipped_img = cropped_img.transpose(Image.FLIP_TOP_BOTTOM)
    else:
        flipped_img = cropped_img

        # -----------------------------
    # SAVE PROCESSED IMAGE INTO SUBFOLDERS
    # -----------------------------
    # Hole_Type determines subfolder: "Cal-dot", "Guard-ring", "Default"
    save_subfolder = os.path.join(PROCESSED_DIR, Hole_Type)
    os.makedirs(save_subfolder, exist_ok=True)

    # Build filename: Module_Cell_processed.png
    base_name = os.path.splitext(Image_Name)[0]
    new_name = f"{Current_Module}_{base_name}_processed.png"

    save_path = os.path.join(save_subfolder, new_name)
    flipped_img.save(save_path)

    print(f"Saved processed image: {save_path}")

    return save_path


def get_unprocessed_images(module_name):
    raw_path = os.path.join(RAW_DIR, module_name)
    raw_files = [f for f in os.listdir(raw_path) if f.lower().endswith(".png")]

    # Collect ALL processed filenames from ALL subfolders
    processed_files = []
    for root, dirs, files in os.walk(PROCESSED_DIR):
        for f in files:
            processed_files.append(f)

    unprocessed = []

    for raw in raw_files:
        base = os.path.splitext(raw)[0]  # "1_13_14"
        expected = f"{module_name}_{base}_processed.png"

        if expected not in processed_files:
            unprocessed.append(raw)

    print("Unprocessed images for module", module_name, ":", unprocessed)
    return unprocessed


def get_all_modules():
    return [
        d for d in os.listdir(RAW_DIR)
        if os.path.isdir(os.path.join(RAW_DIR, d))
    ]

def get_modules_with_unprocessed():
    modules = get_all_modules()
    todo_modules = []

    for module in modules:
        unprocessed = get_unprocessed_images(module)
        if len(unprocessed) > 0:
            todo_modules.append(module)

    return todo_modules

for module in get_modules_with_unprocessed():
    unprocessed = get_unprocessed_images(module)
    
    for img in unprocessed:
        #print(input(f"Processing module {module} with {len(unprocessed)} unprocessed images. Press Enter to continue..."))
        processed_img = Main(module, img)      # <-- PROCESS

