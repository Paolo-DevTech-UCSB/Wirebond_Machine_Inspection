from PIL import Image, ImageDraw
import os
import Inital_Image_Processor_DSKTP as IIP
import Image_Processing_Tools as IPT
from wb_config import RAW_DIR, PROCESSED_DIR


def Main_Process(Current_Module, Image_Name):
    count2 = 0
    img = IPT.Load_Img(RAW_DIR, Current_Module, Image_Name)
    if img is None:
        return 
    Thin_Crop_Img = IPT.Img_Crop(img, 350, 350, 700, 850)
    x_center, y_center, count = IPT.compute_darks_com(Thin_Crop_Img)

    if 500 < x_center < 1200 and 400 < y_center < 1000: Center_Tol = True
    else: Center_Tol = False

    if count < 500 or Center_Tol == False:
        x_center, y_center, count2 = IPT.compute_sensor_com(Thin_Crop_Img)
    x_center = 350 + x_center; y_center = 350 + y_center

    # (tested with 6/6) Centers were "close" to merc center
    Classification_Crop = IPT.Img_Crop(img, x_center, y_center, 400, 400)
    Classification_Crop.show
    Image_Type = IPT.Classify_Img(Thin_Crop_Img, 0, 0)
    print("Image Name:", Image_Name, "Type:", Image_Type)
    print(input("next..."))



def Main_Controller():
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

    for module in get_modules_with_unprocessed():            #each module is a folder --> makes a unprocessed list
        unprocessed = get_unprocessed_images(module)         #each Each unprocessed list (module) --> makes a list of images to process
        
        for img in unprocessed:
            processed_img = Main_Process(module, img)  



Main_Controller()




