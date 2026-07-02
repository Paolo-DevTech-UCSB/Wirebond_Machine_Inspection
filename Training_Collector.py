import Folder_to_Report_config as config
import os
import re
import shutil
from Text_Report import Main

def get_module_subfolders():

    module_subfolders = []
    processed_modules_path = os.path.join(config.CONFIG["BASE_DIR"], config.CONFIG["REPORT_DIR"])
    # os.scandir looks ONLY at the top level of the directory
    with os.scandir(processed_modules_path) as entries:
        for entry in entries:
            if entry.is_dir():
                module_subfolders.append(entry.name)

    print("Module subfolders in the report directory:")
    for folder in module_subfolders:
        print(f" - {folder}")


    return module_subfolders


def Move_Needed_Classes(module):
    images_list = []
    flags_list = []
    duplicates = []
    cleared_flags = []
    photos_path = os.path.join(config.CONFIG["BASE_DIR"], config.CONFIG["REPORT_DIR"], module)
    New_Training_Path = os.path.join(config.CONFIG["BASE_DIR"], config.CONFIG["NEW_TRAINING_DIR"], "images")
    
    # Loop through the generator to unpack its contents
    for root, dirs, files in os.walk(photos_path):
        for file in files:
            # Optional: Only grab actual image files
            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                images_list.append(file)

    #print(f"Images in the module '{module}':")
    #for file in images_list:
    #    print(file)

    report_file_path = os.path.join(config.CONFIG["BASE_DIR"], config.CONFIG["REPORT_DIR"], module, "module_report.txt")
    with open(report_file_path, "r") as f:
        report_content = f.read()

    for line in report_content.split('\n'):
        for img in images_list:
            if img in line:
                if img not in duplicates:
                    flags_list.append(img)
                duplicates.append(img)

    print(f"Flags in the module '{module}':")
    for flag in flags_list:
        print(flag)

    #REMOVE ALL PREEXISTING FILES IN THE NEW TRAINING FOLDER BEFORE MOVING NEW FILES
    for flag in flags_list:
        destination_path = os.path.join(New_Training_Path, flag)
        if not os.path.exists(destination_path):
            cleared_flags.append(flag)
            


    for flag in cleared_flags:
        Pass = input(f"Do you want to move the flagged image '{flag}' to the New Training folder? (y/n): ")
        if Pass.lower() == 'y':
            PassBool = True
        else:  
            PassBool = False

        if PassBool:
            source_path = os.path.join(photos_path, flag)
            destination_path = os.path.join(New_Training_Path, flag)

            if not os.path.exists(New_Training_Path):
                os.makedirs(New_Training_Path)

            if os.path.exists(source_path):
                shutil.copy2(source_path, destination_path)
                print(f"Copied '{flag}' to the New Training folder.")
            else:
                print(f"File '{flag}' does not exist in the source folder.")






#USING GEMINI"S VERSION: MAY ONLY BE READY ONE REPORT FILE, NEEDS TO BE MODIFIED TO READ ALL RELEVANT REPORT FILES IN THE REPORT FOLDER
def make_yolo_labels():
    New_Training_Path = os.path.join(config.CONFIG["BASE_DIR"], config.CONFIG["NEW_TRAINING_DIR"])
    images_list = []
    
    # 1. Gather all images
    for root, dirs, files in os.walk(New_Training_Path):
        for file in files:
            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                images_list.append(file)

    # 2. Read all report files
    report_files = []
    for root, dirs, files in os.walk(os.path.join(config.CONFIG["BASE_DIR"], config.CONFIG["REPORT_DIR"])):
        for file in files:
            if file.endswith(".txt"):
                report_files.append(os.path.join(root, file))

    report_lines = []
    for report_file_path in report_files:
        with open(report_file_path, "r") as f:
            report_lines.extend(f.readlines())

    # Define YOLO class IDs
    class_mapping = {
        "debris": 0,
        "disfigured_bond": 1,
        "missing_bond": 2,
        "tape_in_hole": 3,
        "three_bonds": 4
    }

    # Dictionary to hold parsed data: { "filename.png": [ (class_id, [x1, y1, x2, y2]), ... ] }
    image_annotations = {}
    parsing_detections = False
    current_category = None

    # 3. Parse the report
    for line in report_lines:
        line = line.strip()
        if not line:
            continue

        # Wait until we hit the relevant section
        if line == "Images with detections:":
            parsing_detections = True
            continue

        if parsing_detections:
            # Check if line is a category header (e.g., "tape_in_hole:")
            if line.endswith(":") and " " not in line:
                category_name = line[:-1] # Remove the colon
                current_category = class_mapping.get(category_name)
                continue

            # Check if the line is an image entry with coordinates
            if current_category is not None and line.endswith("]"):
                # Split the filename from the bounding boxes
                parts = line.split(" ", 1)
                
                if len(parts) == 2:
                    filename = parts[0]
                    boxes_str = parts[1]

                    # Use regex to find all boxes enclosed in brackets
                    # This safely handles lines with multiple boxes
                    boxes = re.findall(r'\[(.*?)\]', boxes_str)

                    if filename not in image_annotations:
                        image_annotations[filename] = []

                    for box in boxes:
                        # Convert string "189.22, 376.61..." into a list of floats
                        coords = [float(x.strip()) for x in box.split(',')]
                        image_annotations[filename].append((current_category, coords))

    # 4. Generate the YOLO .txt label files
    IMG_WIDTH = 600
    IMG_HEIGHT = 600

    # 4. Generate the YOLO .txt label files
    for image_name in images_list:
        if image_name in image_annotations:
            
            # --- Ensure the directory exists ---
            labels_dir = os.path.join(New_Training_Path, "labels")
            os.makedirs(labels_dir, exist_ok=True)
            
            label_filename = os.path.splitext(image_name)[0] + ".txt"
            label_path = os.path.join(labels_dir, label_filename)

            # --- Write the normalized 8-point polygon format ---
            with open(label_path, "w") as label_file:
                for class_id, coords in image_annotations[image_name]:
                    xmin, ymin, xmax, ymax = coords

                    # 1. Normalize against the fixed 600x600 dimensions
                    n_xmin = xmin / IMG_WIDTH
                    n_ymin = ymin / IMG_HEIGHT
                    n_xmax = xmax / IMG_WIDTH
                    n_ymax = ymax / IMG_HEIGHT
                    
                    # 2. Map to the 4 corners (Clockwise starting Top-Left)
                    x1, y1 = n_xmin, n_ymin  # Top-Left
                    x2, y2 = n_xmax, n_ymin  # Top-Right
                    x3, y3 = n_xmax, n_ymax  # Bottom-Right
                    x4, y4 = n_xmin, n_ymax  # Bottom-Left

                    # 3. Write out to the file matching the old format
                    label_file.write(f"{class_id} {x1:.16f} {y1:.16f} {x2:.16f} {y2:.16f} {x3:.16f} {y3:.16f} {x4:.16f} {y4:.16f}\n")
        








def Main():
    module_subfolders = get_module_subfolders()
    for module in module_subfolders:
        Move_Needed_Classes(module)
    make_yolo_labels()

Main()
