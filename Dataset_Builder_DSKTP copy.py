from PIL import Image
import os
import Inital_Image_Processor_DSKTP as IIP
from wb_config import RAW_DIR, PROCESSED_DIR

def Main(Current_Module, Image_Name):

    # Load raw image
    img_path = os.path.join(RAW_DIR, Current_Module, Image_Name)
    img = Image.open(img_path)

    # Get offsets + flip flag
    PCBX, PCBY, more_above = IIP.Main(Current_Module, Image_Name)

    # Crop
    cropped_img = img.crop((400 + PCBX, 375 + PCBY, 1400 + PCBX, 1200 + PCBY))

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

Image_List = ["10_22_23.png", "1_13_14.png", "2_3_15.png", "11_12_24.png"]

for image_name in Image_List:
    Main("MHF1WCSB0005", image_name)

