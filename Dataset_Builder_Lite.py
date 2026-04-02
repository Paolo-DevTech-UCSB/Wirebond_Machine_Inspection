from PIL import Image, ImageDraw
import os
import Image_Processing_Tools as IPT
from wb_config import RAW_DIR, PROCESSED_DIR
import numpy as np


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

    #Translate Center (Wrt thin) ---> Center (wrt full image)
    full_Im_x = x_center + 350; full_im_y = y_center + 350
    #print(full_Im_x, full_im_y)
    
    #Set Crop boundaries WRT full image center
    West = full_Im_x - 300; East = full_Im_x + 100; North = full_im_y - 300; South = full_im_y + 100

    # (tested with 6/6) Centers were "close" to merc center
    PreClassification_Crop = IPT.Img_Crop(img, West, North, 600, 600)
    #PreClassification_Crop.show()

    #getting new sensor center from PCC
    PCC_Center_x, PCC_Center_y, count = IPT.compute_sensor_com(PreClassification_Crop)

    #Translate PCC Center to (WRT) Full Img 
    im_center_X = PCC_Center_x  + West; im_center_Y = PCC_Center_y + North

    #Set Tight Crop Boundaries:
    Left = im_center_X - 300; Top = im_center_Y - 300; 
    if Top < 350:
        heightbonus = 350 - Top
        Top = 350
    else:
        heightbonus = 0

    
    Classification_Crop = IPT.Img_Crop(img, Left, Top, 600, 600 + heightbonus)
    #Classification_Crop.show()
    
    Image_Type = IPT.Classify_Img(Classification_Crop, 0, 0)
    print("Image Name:", Image_Name, "Type:", Image_Type)
    #print(input("next..."))
    # tested: 

    ##---CLASSIFICATION COMPLETE ---> Moving To Photoprep 

    if Image_Type == "Cal-dot":
        #center on combined gold and sensor
        Processed_Center_X, Processed_Center_Y, count = IPT.compute_combined_com(Classification_Crop)
        moreAbove = False
    elif Image_Type == "Guard-ring":
        #center on Gold COM
        Processed_Center_X, Processed_Center_Y, count = IPT.compute_gold_com(Classification_Crop)
        moreAbove = False
    elif Image_Type == "Default":
        #Center on Mercedes
        lines = IPT.Detect_Merc_Center(Classification_Crop, False)
        if len(lines) > 1: 
            print("this is len(lines):", len(lines))
            input("Showing Detected Lines, press Enter to continue...")
        elif len(lines) == 1:
            print("Only one spoke detected, attempting to find others...")
            (_, (Gx1, Gy1, Bx1, By1)) = lines[0]
            X_1, Y_1 = Bx1, By1
            X_2, Y_2 = Gx1, Gy1

            lines = IPT.find_other_spokes(X_1, X_2, Y_1, Y_2, Classification_Crop)

        elif len(lines) == 0:
            print("COMPLETE DMC FAILURE, no spokes found")
            return 0

        #There needs to be a single line check, and a interspection finder based #1 and a fake.
        IPT.show_lines_on_crop(Classification_Crop, lines)

        Processed_Center_X, Processed_Center_Y = IPT.get_center_from_spokes(lines)
        #print("This is lines:", lines)

        Processed_Center_X += Left
        Processed_Center_Y += Top
        #print(lines)
        #print(type(lines[0]))

        
        if len(lines) < 3:
            (_, (Gx1, Gy1, Bx1, By1)) = lines[0]
            X_1, Y_1 = Bx1, By1
            X_2, Y_2 = Gx1, Gy1

            lines = IPT.find_other_spokes(X_1, X_2, Y_1, Y_2, Classification_Crop)

        center = IPT.get_center_from_spokes(lines)
        if center is None or center == (None, None):
            print("DMC Failed: could not compute center from spokes")
            Processed_Center_X = 0
            Processed_Center_Y = 0
        else:
            Processed_Center_X, Processed_Center_Y = center
            # Mercedes center is relative to Classification_Crop
            # Translate to full image coordinates
            Processed_Center_X = Processed_Center_X + Left
            Processed_Center_Y = Processed_Center_Y + Top


    else:
        Processed_Center_X = 0; Processed_Center_Y = 0
        print("Photo Type:", Image_Type, "Not recognized")

    # Center is already translated to full-image coordinates earlier
    Last_Center_X = float(Processed_Center_X)
    Last_Center_Y = float(Processed_Center_Y)

    Final_West  = Last_Center_X - 300
    Final_North = Last_Center_Y - 300

    print("Final Center:", (Last_Center_X, Last_Center_Y))

    Final_West = Last_Center_X - 300; Final_North = Last_Center_Y - 300
    
    Processed_Crop = IPT.Img_Crop(img, Final_West, Final_North, 600, 600)
    
    def more_above_midpoint(lines):
        above_count = 0

        for label, (x1, y1, x2, y2) in lines:
            mid_y = (y1 + y2) / 2
            if mid_y < 0:
                above_count += 1

        return above_count >= 2
    
    moreAbove = more_above_midpoint(lines)

    save_processed_image(Processed_Crop, Image_Type, Current_Module, Image_Name, moreAbove)

def save_processed_image(Processed_Crop, Image_Type, Current_Module, Image_Name, moreAbove):
    if moreAbove:
        Processed_Crop = Processed_Crop.transpose(Image.FLIP_TOP_BOTTOM)

    save_subfolder = os.path.join(PROCESSED_DIR, Image_Type)
    os.makedirs(save_subfolder, exist_ok=True)

    # Build filename: Module_Cell_processed.png
    base_name = os.path.splitext(Image_Name)[0]
    new_name = f"{Current_Module}_{base_name}_processed.png"

    save_path = os.path.join(save_subfolder, new_name)
    Processed_Crop.save(save_path)

    print(f"Saved processed image: {save_path}")

    return save_path




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
            print("Saved Photo:", processed_img)



Main_Controller()




