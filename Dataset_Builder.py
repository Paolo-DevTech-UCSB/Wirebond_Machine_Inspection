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
        Processed_Center_X, Processed_Center_Y, moreAbove = IPT.Detect_Merc_Center(Classification_Crop, True)
    else:
        Processed_Center_X = 0; Processed_Center_Y = 0
        print("Photo Type:", Image_Type, "Not recognized")

    Last_Center_X = Processed_Center_X  + Left; Last_Center_Y = Processed_Center_Y + North

    Final_West = Last_Center_X - 300; Final_North = Last_Center_Y - 300
    
    Processed_Crop = IPT.Img_Crop(img, Final_West, Final_North, 600, 600)

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




