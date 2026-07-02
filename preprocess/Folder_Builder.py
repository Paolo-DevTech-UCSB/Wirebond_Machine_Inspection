from PIL import Image, ImageDraw
import os
import preprocess.Image_Processing_Tools as IPT
#from wb_config import RAW_DIR, PROCESSED_DIR
import numpy as np
from preprocess.orientation_verification import verify_orientation
import preprocess.SetQuality_Checker as SetQuality_Checker
from Folder_to_Report_config import CONFIG


def get_module_paths(module_name):
    base = CONFIG["BASE_DIR"]

    # Input folder for this module
    module_input = os.path.join(base, CONFIG["INPUT_DIR"], module_name)

    # Output folder for this module
    module_processed_root = os.path.join(base, CONFIG["PROCESSED_DIR"], module_name)

    # Ensure module processed root exists
    os.makedirs(module_processed_root, exist_ok=True)

    # Create the four classification folders inside the processed folder
    module_output = {
        folder: os.path.join(module_processed_root, folder)
        for folder in CONFIG["MODULE_OUTPUT_FOLDERS"]
    }

    for path in module_output.values():
        os.makedirs(path, exist_ok=True)

    return module_input, module_output


def Main_Process(Current_Module, Image_Name):

    print("MAIN PROCESS IS CALLED @COPIOLET")

    Current_Module = Current_Module 
    Image_Name = Image_Name
    lines = []   # <--- ADD THIS
    orientation = "upright"  # safe default
    count2 = 0
    module_input, module_output = get_module_paths(Current_Module)
    img_path = os.path.join(module_input, Image_Name)
    img = IPT.Load_Img(img_path)

    img = IPT.Load_Img(img_path)

    # Case 1: PIL couldn't even open the file
    if img is None:
        print(f"[ERROR] Could not open image: {img_path}")
        return save_processed_image(None, "Unprocessed", Current_Module, Image_Name, False)

    # Case 2: PIL opened the header, but the image data is corrupted
    try:
        img.load()   # force full decode
    except Exception as e:
        print(f"[ERROR] Corrupted image detected: {img_path}")
        print(e)
        return save_processed_image(None, "Unprocessed", Current_Module, Image_Name, False)

    Thin_Crop_Img = IPT.Img_Crop(img, 350, 350, 700, 850)
    x_center, y_center, count = IPT.compute_darks_com(Thin_Crop_Img)

    print(">>> DEBUG: RETURN triggered at LINE X")


    if x_center is None or y_center is None:
        Image_Type = "Unprocessed"
        saved_path = save_processed_image(Thin_Crop_Img, "Unprocessed", Current_Module, Image_Name, False)
        return saved_path

    if 500 < x_center < 1200 and 400 < y_center < 1000: Center_Tol = True
    else: Center_Tol = False

    print(">>> DEBUG: RETURN triggered at LINE X")


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

    print("Crop bounds:", Left, Top, 600, 600 + heightbonus)

    Classification_Crop = IPT.Img_Crop(img, Left, Top, 600, 600 + heightbonus)

    print("\n[DEBUG] Full image size:", img.size)
    #print("[DEBUG] Classification_Crop size:", Classification_Crop.size)
    print("[DEBUG] Left, Top used for crop:", Left, Top)
    #Classification_Crop.show()
    
    print(">>> DEBUG: RETURN triggered at LINE X")


    #SetQuality_Checker.debug_integral_bands(img)
    if SetQuality_Checker.garbage_filter(img):
        Image_Type = "Unprocessed"
    else:
        Image_Type = IPT.Classify_Img(Classification_Crop, 0, 0)

    print(">>> DEBUG: Image_Type is:", Image_Type)

    #print(input("next..."))
    # tested: 

    ##---CLASSIFICATION COMPLETE ---> Moving To Photoprep 

    if Image_Type == "Cal-dot":
        # center on combined gold and sensor
        Processed_Center_X, Processed_Center_Y = IPT.compute_combined_com(Classification_Crop)
        #print("[DEBUG] Classification_Crop size:", Classification_Crop.size)
        print("[DEBUG] COM inside Classification_Crop:", Processed_Center_X, Processed_Center_Y)

        # translate to full-image coordinates
        Processed_Center_X += Left
        Processed_Center_Y += Top
        print("[DEBUG] COM translated to full image:", Processed_Center_X, Processed_Center_Y)

        moreAbove = False

    elif Image_Type == "Guard-ring":    
        # center on Gold COM
        Processed_Center_X, Processed_Center_Y, count = IPT.compute_gold_com(Classification_Crop)
        #print("[DEBUG] Classification_Crop size:", Classification_Crop.size)
        print("[DEBUG] COM inside Classification_Crop:", Processed_Center_X, Processed_Center_Y)

        # translate to full-image coordinates
        Processed_Center_X += Left
        Processed_Center_Y += Top
        print("[DEBUG] COM translated to full image:", Processed_Center_X, Processed_Center_Y)

        moreAbove = False 
    elif Image_Type == "Default":
        #Center on Mercedes
        lines, orientation = IPT.Detect_Merc_Center(Classification_Crop, False, mode="Default")
        if len(lines) < 3:
            lines, orientation = IPT.Detect_Merc_Center(Classification_Crop, False, mode="Sensor")

        if len(lines) == 3: 
            print("this is len(lines):", len(lines))
            #input("Showing Detected Lines, press Enter to continue...")
        elif len(lines) == 2:
            lines = IPT.infer_missing_spoke_from_two(lines, Classification_Crop)
            print("Only two spokes detected, inferring third spoke...")
        
        elif len(lines) == 1:
            print("Only one spoke detected, attempting to find others...")
            (_, (Gx1, Gy1, Bx1, By1)) = lines[0]
            X_1, Y_1 = Bx1, By1
            X_2, Y_2 = Gx1, Gy1

            lines = IPT.find_other_spokes(X_1, X_2, Y_1, Y_2, Classification_Crop)

        elif len(lines) == 0:
            print("COMPLETE DMC FAILURE, Save to Unprocessed folder for manual review")
            saved_path = save_processed_image(Classification_Crop, "Unprocessed", Current_Module, Image_Name, False)

        #There needs to be a single line check, and a interspection finder based #1 and a fake.
        #IPT.show_lines_on_crop(Classification_Crop, lines)


        center = IPT.get_center_from_spokes(lines)
        Processed_Center_X, Processed_Center_Y = center[0], center[1]
        #print("This is lines:", lines)

        print(">>> DEBUG: RETURN triggered at LINE X")


        if Processed_Center_X is None or Processed_Center_Y is None:
            print("DMC Failed: Saving to Unprocessed folder for manual review")
            saved_path = save_processed_image(Classification_Crop, "Unprocessed", Current_Module, Image_Name, False)
            Processed_Center_X = 0
            Processed_Center_Y = 0
        Processed_Center_X += Left
        Processed_Center_Y += Top
        #print(lines)
        #print(type(lines[0]))


        

        """Processed_Center_X, Processed_Center_Y = center
        # Mercedes center is relative to Classification_Crop
        # Translate to full image coordinates
        Processed_Center_X = Processed_Center_X + Left
        Processed_Center_Y = Processed_Center_Y + Top"""

        #print(">>> DEBUG: RETURN triggered at LINE X")


    elif Image_Type == "Unprocessed":
        print("Photo Type: Unprocessed, skipping processing and saving to Unprocessed folder")
        saved_path = save_processed_image(Classification_Crop, "Unprocessed", Current_Module, Image_Name, False)
       
        print(">>> DEBUG: RETURN triggered at LINE X")
        return saved_path
    else:
        Processed_Center_X = 0; Processed_Center_Y = 0
        print("Photo Type:", Image_Type, "Not recognized")


    print(">>> DEBUG: Image_Type is:", Image_Type)


    # Center is already translated to full-image coordinates earlier
    Last_Center_X = float(Processed_Center_X)
    Last_Center_Y = float(Processed_Center_Y)

    Final_West  = Last_Center_X - 300
    Final_North = Last_Center_Y - 300

    print("Final Center:", (Last_Center_X, Last_Center_Y))

    Final_West = Last_Center_X - 300; Final_North = Last_Center_Y - 300
    
    Processed_Crop = IPT.Img_Crop(img, Final_West, Final_North, 600, 600)
    #IPT.show_lines_on_crop(Processed_Crop, lines)
    #print("these are thelines being used in the plotter before the ray plotter:", lines)    

    if not isinstance(Processed_Crop, np.ndarray):
        Processed_Crop_RAY = np.array(Processed_Crop)

    rays = []
    for i, line in enumerate(lines):
        split_point = np.array([
            Last_Center_X - Final_West,
            Last_Center_Y - Final_North
            ])
        ray_dir = IPT.determine_spoke_ray_direction(line, split_point, Processed_Crop_RAY, 200, 50)
        rays.append({
            "line": line,
            "Center Point": split_point,
            "ray_dir": ray_dir
        })

    #print("This is rays: ", rays)

    if Image_Type == "Default":      
        moreAbove = (orientation == "upside_down")
        score = verify_orientation(Processed_Crop)
        print(f"[DEBUG] Mercedes correlation score: {score:.3f}")
        score_upright = verify_orientation(Processed_Crop)
        # Try flipped version
        flipped = Processed_Crop.rotate(180)
        score_flipped = verify_orientation(flipped)
        # Pick whichever orientation matches the mask better
        if score_flipped > score_upright:
            print(f"[DEBUG] Flipped orientation chosen ({score_flipped:.3f} > {score_upright:.3f})")
            Processed_Crop = flipped
            moreAbove = False
        else:
            print(f"[DEBUG] Upright orientation chosen ({score_upright:.3f} >= {score_flipped:.3f})")
            moreAbove = False  # because we are saving the corrected version

            # save again or overwrite


        saved_path = save_processed_image(Processed_Crop, Image_Type, Current_Module, Image_Name, moreAbove)
        return saved_path
    elif Image_Type != "Unprocessed":
        saved_path = save_processed_image(Processed_Crop, Image_Type, Current_Module, Image_Name, False)
        return saved_path
    else:  # Image_Type == "Unprocessed"
        saved_path = save_processed_image(Processed_Crop, "Unprocessed", Current_Module, Image_Name, False)
        return saved_path

def detect_orientation_by_dark_weight(img, cx, cy, threshold=150):
    width, height = img.size
    pixels = img.load()

    top_dark = 0
    bottom_dark = 0

    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            is_dark = (r < threshold and g < threshold and b < threshold)

            if is_dark:
                if y < cy:
                    top_dark += 1
                else:
                    bottom_dark += 1

    # If the top half is darker → image is upside down
    return "upside_down" if top_dark > bottom_dark else "upright"




def more_above2(rays):
    """
    rays: list of dicts:
        {
            "line": ("L1", (x1,y1,x2,y2)),
            "intersection": (ix, iy),
            "ray_dir": (dx, dy)
        }

    Returns the index of the spoke that is most 'above'
    (i.e., smallest dy).
    """

    best_idx = None
    best_value = float('inf')

    for i, r in enumerate(rays):
        dx, dy = r["ray_dir"]
        if dy < best_value:
            best_value = dy
            best_idx = i


    def debug_plot_rays_fixed(rays, title="Ray Orientation Debug"):
        import matplotlib.pyplot as plt
        import numpy as np

        plt.figure(figsize=(6,6))
        plt.title(title)
        ax = plt.gca()
        ax.set_aspect('equal', adjustable='box')
        ax.invert_yaxis()

        colors = ['red', 'green', 'blue']

        for i, r in enumerate(rays):
            line = r["line"]
            ray = r["ray_dir"]
            center = r["Center Point"]  # this is your COM

            #print(f"(LATEST DEBUG)  Ray {i}: direction = {ray}, center = {center}")

            # project center onto the line
            _, (x1, y1, x2, y2) = line
            p1 = np.array([x1, y1], float)
            p2 = np.array([x2, y2], float)
            v = p2 - p1
            v = v / np.linalg.norm(v)

            S = np.array(center, float)
            t = np.dot(S - p1, v)
            I = p1 + v * t  # projection ON the line

            # draw the line
            plt.plot([x1, x2], [y1, y2], color=colors[i], alpha=0.3)

            # draw the ray from the SAME anchor point
            p1 = I
            p2 = I + ray * 200
            plt.arrow(p1[0], p1[1],
                    ray[0]*200, ray[1]*200,
                    head_width=15, head_length=20,
                    color=colors[i], length_includes_head=True)

            plt.text(p2[0], p2[1], f"Ray {i}", color=colors[i], fontsize=12)

        plt.grid(True)
        #plt.show()

    #debug_plot_rays_fixed(rays)




    return best_idx




def more_above(lines, debug=False):
    angles = []

    if debug:
        print("\n=== ORIENTATION DEBUG ===")

    for name, (x1, y1, x2, y2) in lines:
        ang = np.arctan2(y2 - y1, x2 - x1)
        angles.append(ang)

        if debug:
            deg = np.degrees(ang)
            print(f"{name}: ({x1:.1f},{y1:.1f}) → ({x2:.1f},{y2:.1f})  angle = {deg:+.2f}°")

    # "Upward" in image coords: -90° to +90°
    upward_count = sum(-np.pi/2 <= a <= np.pi/2 for a in angles)

    is_upright = (upward_count <= 1)

    
    if debug:
        print(f"Upward spokes: {upward_count} out of {len(angles)}")
        print("Orientation:", "UPRIGHT (Y)" if is_upright else "UPSIDE-DOWN (peace)")
        print("==========================\n")

    return is_upright




def save_processed_image(Processed_Crop, Image_Type, Current_Module, Image_Name, moreAbove):
    # Determine save directory
    module_input, module_output = get_module_paths(Current_Module)
    save_dir = module_output.get(Image_Type, module_output["Unprocessed"])
    os.makedirs(save_dir, exist_ok=True)

    # Build filename
    base_name = os.path.splitext(Image_Name)[0]
    new_name = f"{Current_Module}_{base_name}_processed.png"
    save_path = os.path.join(save_dir, new_name)

    # If the image is None, create a placeholder or skip saving
    if Processed_Crop is None:
        print(f"[WARNING] No image to save for {Image_Name}. Creating placeholder.")
        # Create a 1×1 black pixel placeholder so the pipeline stays consistent
        placeholder = Image.new("RGB", (1, 1), (0, 0, 0))
        placeholder.save(save_path)
        return save_path

    # Flip if needed
    if moreAbove:
        Processed_Crop = Processed_Crop.transpose(Image.FLIP_TOP_BOTTOM)

    # Save normally
    Processed_Crop.save(save_path)
    print(f"Saved processed image: {save_path}")
    return save_path

def Main_Controller():

    print("MAIN CONTROLLER IS CALLED @COPIOLET")
    # 1. Find all module folders inside the INPUT_DIR
    base_input = os.path.join(CONFIG["BASE_DIR"], CONFIG["INPUT_DIR"])

    modules = [
        d for d in os.listdir(base_input)
        if os.path.isdir(os.path.join(base_input, d))
    ]

    print("Modules found:", modules)

    # 2. Process each module
    for module in modules:
        module_input, module_output = get_module_paths(module)

        # List all raw PNGs inside this module's input folder
        raw_files = [
            f for f in os.listdir(module_input)
            if f.lower().endswith(".png") and "_processed" not in f.lower()
        ]

        # Collect all processed filenames from the module's 4 subfolders
        processed_files = set()
        for folder in module_output.values():
            for f in os.listdir(folder):
                processed_files.add(f)

        # Determine which raw files still need processing
        unprocessed = []
        for raw in raw_files:
            base = os.path.splitext(raw)[0]
            expected = f"{module}_{base}_processed.png"
            if expected not in processed_files:
                unprocessed.append(raw)

        print(f"[{module}] Unprocessed images:", unprocessed)

        # 3. Process each unprocessed image
        for img in unprocessed:
            processed_img = Main_Process(module, img)
            print("Saved Photo:", processed_img)



