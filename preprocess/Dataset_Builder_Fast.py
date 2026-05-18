from PIL import Image, ImageDraw
import os
import preprocess.Image_Processing_Tools as IPT
from preprocess.SetQuality_Checker import compute_new_center, debug_integral_bands
import numpy as np
from preprocess.orientation_verification import verify_orientation
import preprocess.SetQuality_Checker as SetQuality_Checker
from Folder_to_Report_config import CONFIG
import os

RAW_DIR = os.path.join(CONFIG["BASE_DIR"], CONFIG["INPUT_DIR"])
PROCESSED_DIR = os.path.join(CONFIG["BASE_DIR"], CONFIG["PROCESSED_DIR"])

def classify_from_filename(Image_Name):
    """
    Determine the image category based on filename.
    '0' is treated as a placeholder and ignored.
    """

    # Remove extension and split by underscores
    base = os.path.splitext(Image_Name)[0]
    parts = base.split("_")

    # Extract numeric parts AND ignore zeros
    numeric_parts = [p for p in parts if p.isdigit() and p != "0"]

    count = len(numeric_parts)

    # ------------------------------------------------------------
    # RULE 1 — Three REAL numeric IDs → DEFAULT
    # ------------------------------------------------------------
    if count == 3:
        return "Default"

    # ------------------------------------------------------------
    # RULE 2 — One REAL numeric ID → Cal-dot or Guard-ring
    # ------------------------------------------------------------
    if count == 1:
        return "Unknown"   # You can refine this later

    # ------------------------------------------------------------
    # RULE 3 — Two REAL numeric IDs → Unknown for now
    # ------------------------------------------------------------
    if count == 2:
        return "Unknown"

    # ------------------------------------------------------------
    # RULE 4 — No real IDs → Unknown
    # ------------------------------------------------------------
    return "Unknown"

def Main_Process(Current_Module, Raw_Image_Name, Module_Center=None):
    """
    NEW VERSION — CLEAN, FAST, CATEGORY-FIRST PIPELINE
    --------------------------------------------------
    1. Load image
    2. Determine category from filename
    3. Run category-specific centering function
    4. Crop around center
    5. Save processed image
    """

    # ------------------------------------------------------------
    # STEP 1 — Load the raw image
    # ------------------------------------------------------------
    full_path = os.path.join(RAW_DIR, Current_Module, Raw_Image_Name)
    print("[DEBUG] Loading:", full_path)

    img = IPT.Load_Img(full_path)

    if img is None:
        print(f"[ERROR] Could not load image: {full_path}")
        return None

    # ------------------------------------------------------------
    # STEP 2 — Determine category from filename
    # ------------------------------------------------------------
    category = classify_from_filename(Raw_Image_Name)
    print(f"[INFO] Category from filename: {category}")

    # ------------------------------------------------------------
    # STEP 3 — Run category-specific center finder
    # ------------------------------------------------------------
    if category == "Cal-dot":
        center_x, center_y = center_cal_dot(img)

    elif category == "Guard-ring":
        center_x, center_y = center_guard_ring(img)

    elif category == "Default":
        #cx_blend, cy_blend = Module_Center
        if Module_Center is None:
            print(f"[WARN] Module center missing — falling back to per-image center")
            #debug_integral_bands(img)
            import matplotlib.pyplot as plt
            plt.show()

            cx_blend, cy_blend = compute_new_center(img)
            if cx_blend is None:
                print("[ERROR] Per-image center failed too — skipping image")
                return None
        else:
            cx_blend, cy_blend = Module_Center


        #import numpy as np
        img_np = np.array(img)
        H_raw, W_raw = img_np.shape[:2]

        scale_y = (H_raw - 350) / 1200
        scale_x = W_raw / 1200

        center_x = cx_blend * scale_x
        center_y = cy_blend * scale_y + 350



    else:
        print("[WARN] Unknown category — saving to Unprocessed.")
        return save_processed_image(img, "Unprocessed", Current_Module, Raw_Image_Name, False)

    # Safety check
    if center_x is None or center_y is None:
        print("[ERROR] Center finder failed — saving to Unprocessed.")
        return save_processed_image(img, "Unprocessed", Current_Module, Raw_Image_Name, False)

    print(f"[INFO] Center found at: ({center_x:.1f}, {center_y:.1f})")





    # ------------------------------------------------------------
    # STEP 4 — Crop around center (600x600)
    # ------------------------------------------------------------
    crop_left = center_x - 300
    crop_top  = center_y - 300

    processed_crop = IPT.Img_Crop(img, crop_left, crop_top, 600, 600)

    # ------------------------------------------------------------
    # STEP 5 — Save processed image
    # ------------------------------------------------------------
    saved_path = save_processed_image(
        processed_crop,
        category,
        Current_Module,
        Raw_Image_Name,
        moreAbove=False
    )

    print(f"[INFO] Saved processed image: {saved_path}")

    return saved_path

def center_cal_dot(img):
    # crop or preprocess if needed
    cx, cy, _ = IPT.compute_combined_com(img)
    return cx, cy
    
def center_guard_ring(img):
    cx, cy, _ = IPT.compute_gold_com(img)
    return cx, cy

def OLD_center_default(img):
    lines, orientation = IPT.Detect_Merc_Center(img, False, mode="Default")

    # fallback to sensor mode if needed
    if len(lines) < 3:
        lines, orientation = IPT.Detect_Merc_Center(img, False, mode="Sensor")

    # infer missing spokes if needed
    if len(lines) == 2:
        lines = IPT.infer_missing_spoke_from_two(lines, img)
    elif len(lines) == 1:
        # reconstruct missing spokes
        (_, (Gx1, Gy1, Bx1, By1)) = lines[0]
        lines = IPT.find_other_spokes(Bx1, Gx1, By1, Gy1, img)

    # if still no lines → fail
    if len(lines) == 0:
        return None, None

    cx, cy = IPT.get_center_from_spokes(lines)
    return cx, cy

def center_default(img, crop_size=600):
    import cv2
    import numpy as np

    # Convert PIL → OpenCV if needed
    if not isinstance(img, np.ndarray):
        img = np.array(img)
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

    H, W = img.shape[:2]

    # -----------------------------------------
    # 1. Crop region used for COM
    # -----------------------------------------
    crop = img[350:, 150:-150]
    ch, cw = crop.shape[:2]

    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)

    # -----------------------------------------
    # 2. Build NOT-green and NOT-gold mask
    # -----------------------------------------
    green_lower1 = np.array([35, 40, 20])
    green_upper1 = np.array([85, 255, 150])
    green_lower2 = np.array([35, 80, 150])
    green_upper2 = np.array([85, 255, 255])
    green_mask = cv2.bitwise_or(
        cv2.inRange(hsv, green_lower1, green_upper1),
        cv2.inRange(hsv, green_lower2, green_upper2)
    )

    gold_lower1 = np.array([15, 120, 150])
    gold_upper1 = np.array([35, 255, 255])
    gold_lower2 = np.array([10, 100, 120])
    gold_upper2 = np.array([25, 255, 255])
    gold_mask = cv2.bitwise_or(
        cv2.inRange(hsv, gold_lower1, gold_upper1),
        cv2.inRange(hsv, gold_lower2, gold_upper2)
    )

    excluded = cv2.bitwise_or(green_mask, gold_mask)
    keep_mask = cv2.bitwise_not(excluded)
    keep_mask = cv2.medianBlur(keep_mask, 5)

    # -----------------------------------------
    # 3. Compute COM
    # -----------------------------------------
    M = cv2.moments(keep_mask)
    if M["m00"] == 0:
        return None, None

    cx_crop = int(M["m10"] / M["m00"])
    cy_crop = int(M["m01"] / M["m00"])

    # -----------------------------------------
    # 4. Convert to full-image coordinates
    # -----------------------------------------
    cx_raw = cx_crop + 150
    cy_raw = cy_crop + 350

    # -----------------------------------------
    # 5. Recenter toward image center (stabilizer)
    # -----------------------------------------
    alpha = 0.35  # 0 = old center, 1 = pure COM
    cx_blend = int((1 - alpha) * (W // 2) + alpha * cx_raw)
    cy_blend = int((1 - alpha) * (H // 2) + alpha * cy_raw)

    # -----------------------------------------
    # 6. Clamp so crop never goes out of bounds
    # -----------------------------------------
    half = crop_size // 2
    cx = max(half, min(cx_blend, W - half))
    cy = max(half, min(cy_blend, H - half))

    return cx, cy



def compute_module_center(module_name, unprocessed_list):
    import numpy as np
    import cv2
    import os
    from PIL import Image

    raw_path = os.path.join(RAW_DIR, module_name)
    imgs = []

    # ------------------------------------------------------------
    # LOAD + PREPROCESS ALL IMAGES FOR THIS MODULE
    # ------------------------------------------------------------
    for fname in unprocessed_list:
        full = os.path.join(raw_path, fname)
        img = cv2.imread(full)

        if img is None:
            continue

        # Crop top 350 px
        img = img[350:, :]

        # Resize to consistent size
        img = cv2.resize(img, (1200, 1200))
        imgs.append(img.astype(np.float32))

    if len(imgs) == 0:
        print(f"[WARN] No images to compile for module {module_name}")
        return None

    # ------------------------------------------------------------
    # BUILD BLENDED MODULE IMAGE (NUMPY, BGR)
    # ------------------------------------------------------------
    compiled = np.mean(imgs, axis=0).astype(np.uint8)

    # ------------------------------------------------------------
    # CONVERT TO PIL RGB FOR CENTER FINDER + DEBUGGER
    # ------------------------------------------------------------
    compiled_rgb = cv2.cvtColor(compiled, cv2.COLOR_BGR2RGB)
    compiled_pil = Image.fromarray(compiled_rgb)

    # ------------------------------------------------------------
    # RUN NEW CENTER FINDER (THIS EXPECTS PIL)
    # ------------------------------------------------------------
    cx, cy = compute_new_center(compiled_pil)

    if cx is None or cy is None:
        debug_integral_bands(compiled_pil)

        import matplotlib.pyplot as plt
        plt.show()   # <-- FORCE debugger window to appear

        print(f"[ERROR] compute_new_center failed for module {module_name}")
        return None



    # ------------------------------------------------------------
    # DRAW OVERLAY (THIS EXPECTS NUMPY)
    # ------------------------------------------------------------
    show_module_center_debug(compiled, int(cx), int(cy), module_name)

    print(f"[MODULE CENTER] {module_name}: ({cx}, {cy})")
    return (cx, cy)


def show_module_center_debug(compiled_img, cx, cy, module_name="Module"):
    """
    Visualizes the compiled module image with the detected center overlaid.
    """
    import cv2
    import matplotlib.pyplot as plt

    # Draw on a copy
    vis = compiled_img.copy()

    if cx is None or cy is None:
        print(f"[ERROR] Cannot draw module center — center is None for {module_name}")
        return


    # Draw center point
    cv2.circle(vis, (cx, cy), 12, (0, 0, 255), -1)

    # Draw crosshair
    cv2.line(vis, (cx - 60, cy), (cx + 60, cy), (0, 0, 255), 3)
    cv2.line(vis, (cx, cy - 60), (cx, cy + 60), (0, 0, 255), 3)

    # Show
    plt.figure(figsize=(6, 6))
    plt.imshow(cv2.cvtColor(vis, cv2.COLOR_BGR2RGB))
    plt.title(f"Module Center Debug: {module_name}\nCenter=({cx}, {cy})")
    plt.axis("off")
    plt.show()






def save_processed_image(Processed_Crop, Image_Type, Current_Module, Raw_Image_Name, moreAbove):
    if moreAbove:
        Processed_Crop = Processed_Crop.transpose(Image.FLIP_TOP_BOTTOM)

    save_subfolder = os.path.join(PROCESSED_DIR, Current_Module, Image_Type)
    os.makedirs(save_subfolder, exist_ok=True)

    # Build filename: Module_Cell_processed.png
    base_name = os.path.splitext(Raw_Image_Name)[0]
    new_name = f"{Current_Module}_{base_name}_processed.png"


    save_path = os.path.join(save_subfolder, new_name)
    Processed_Crop.save(save_path)

    print(f"Saved processed image: {save_path}")

    return save_path

def Main_Controller():
    print("RAW_DIR =", RAW_DIR)
    print("RAW_DIR exists:", os.path.exists(RAW_DIR))
    print("RAW_DIR contents:", os.listdir(RAW_DIR))

    def get_unprocessed_images(module_name):
        raw_path = os.path.join(RAW_DIR, module_name)
        raw_files = [f for f in os.listdir(raw_path) if f.lower().endswith(".png")]

        # Only processed files for THIS module
        module_processed_dir = os.path.join(PROCESSED_DIR, module_name)
        processed_files = []

        if os.path.exists(module_processed_dir):
            for root, dirs, files in os.walk(module_processed_dir):
                processed_files.extend(files)


        # Load module-local Unprocessed folder
        module_processed_dir = os.path.join(PROCESSED_DIR, module_name)
        unprocessed_folder = os.path.join(module_processed_dir, "Unprocessed")

        if not os.path.exists(unprocessed_folder):
            unprocessed_files = set()
        else:
            unprocessed_files = set(os.listdir(unprocessed_folder))

        unprocessed = []

        for raw in raw_files:
            raw_base = os.path.splitext(raw)[0]

            # Check if ANY processed file contains the raw base
            already_processed = any(
                raw_base in f
                for f in processed_files
            )

            # Check if ANY unprocessed file contains the raw base
            already_in_unprocessed = any(
                raw_base in f
                for f in unprocessed_files
            )

            if not already_processed and not already_in_unprocessed:
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
        #each module is a folder --> makes a unprocessed list
        unprocessed = get_unprocessed_images(module)         #each Each unprocessed list (module) --> makes a list of images to process
        
        # NEW: compute module-level center
        module_center = compute_module_center(module, unprocessed)


        for img in unprocessed:
            processed_img = Main_Process(module, img, module_center)  
            print("Saved Photo:", processed_img)

Main_Controller()


