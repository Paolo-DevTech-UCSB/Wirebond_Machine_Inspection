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
    if result == (None, None, None):
        print(f"[SKIP] Could not process {Image_Name} in {Current_Module}")
        return None

    PCBX, PCBY, more_above = result

    # Crop
    cropped_img = img.crop((400 + PCBX, 375 + PCBY,
                            1400 + PCBX, 1200 + PCBY))

    # Flip if needed
    if more_above:
        flipped_img = cropped_img.transpose(Image.FLIP_TOP_BOTTOM)
    else:
        flipped_img = cropped_img

    # -----------------------------
    # SAVE PROCESSED IMAGE (NO SUBFOLDERS)
    # -----------------------------
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    # Build filename: Module_Cell_processed.png
    base_name = os.path.splitext(Image_Name)[0]
    new_name = f"{Current_Module}_{base_name}_processed.png"

    #print("SAVE FUNCTION REACHED")
    save_path = os.path.join(PROCESSED_DIR, new_name)
    flipped_img.save(save_path)

    print(f"Saved processed image: {save_path}")
    #print("Saving to:", save_path)

    return save_path


def get_unprocessed_images(module_name):
    raw_path = os.path.join(RAW_DIR, module_name)
    raw_files = [f for f in os.listdir(raw_path) if f.lower().endswith(".png")]

    processed_files = os.listdir(PROCESSED_DIR)

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

