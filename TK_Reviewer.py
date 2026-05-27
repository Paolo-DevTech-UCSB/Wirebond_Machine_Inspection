import _tkinter as tk
from logging import exception
import os   
from tkinter import font
import tkinter as tk

from matplotlib import lines

basedir = r"C:\Users\hep\Desktop\Basic Inspector\Report Module Folders"
report_dir = basedir


def read_first_module_status(current_module):
    status_path = os.path.join(basedir, current_module, "InspectionStatus.txt")

    if not os.path.exists(status_path):
        #print(f"[DEBUG] Status file missing: {status_path}")
        return None

    with open(status_path, "r") as f:
        lines = f.readlines()

    # No data? (needs at least a header line and one data line)
    if len(lines) < 2:
        #print(f"[DEBUG] Status file has insufficient lines: {len(lines)}")
        return None

    # The first line is the header, so grab the second line
    first_data_line = lines[1].strip()
    if not first_data_line:
        #print("[DEBUG] First data line is empty.")
        return None

    # Parse CSV-style row
    parts = [p.strip() for p in first_data_line.split(",")]
    
    # Catch situations where the line doesn't have all 4 columns yet
    if len(parts) < 4:
        #print(f"[DEBUG] Malformed line in status file: '{first_data_line}'")
        return None

    try:
        # Return as a dict for convenience
        return {
            "original_index": int(parts[0]),
            "image_name": parts[1],
            "grade": int(parts[2]),
            "sorted_index": int(parts[3])
        }
    except ValueError as e:
        #   print(f"[DEBUG] Failed to parse integers from line: {e}")
        return None

#import os

def Stamp_All_Complete(current_module, target_imgname):
    reportlocation = os.path.join(basedir, current_module, "InspectionStatus.txt")
    if not os.path.exists(reportlocation):
        #print(f"[DEBUG] Status file missing: {status_path}")
        return None

    # 1. Read all lines
    with open(reportlocation, 'r') as file:
        lines = file.readlines()

    updated_any = False

    # 2. Rewrite file
    with open(reportlocation, 'w') as file:
        for raw_line in lines:
            line = raw_line.strip()
            if not line:
                continue  # skip blank lines

            parts = line.split(',')

            # Guard against malformed lines
            if len(parts) < 2:
                file.write(line + '\n')
                continue


            if ' Reviewed' not in parts:
                file.write(line + ', Reviewed\n')
            else:
                file.write(line + '\n')
            updated_any = True


    # Optional: let yourself know if nothing matched
    # print("Updated:", updated_any)



def Stamp_Image_Complete(current_module, target_imgname):
    reportlocation = os.path.join(basedir, current_module, "InspectionStatus.txt")
    if not os.path.exists(reportlocation):
        #print(f"[DEBUG] Status file missing: {status_path}")
        return None

    # 1. Read all lines
    with open(reportlocation, 'r') as file:
        lines = file.readlines()

    updated_any = False

    # 2. Rewrite file
    with open(reportlocation, 'w') as file:
        for raw_line in lines:
            line = raw_line.strip()
            if not line:
                continue  # skip blank lines

            parts = line.split(',')

            # Guard against malformed lines
            if len(parts) < 2:
                file.write(line + '\n')
                continue

            # DEBUG: see what we're matching
            print("Checking line parts:", parts, "against target:", target_imgname)

            if parts[1].replace(" ", "") == target_imgname:
                #print("LINE PARTS:", parts, "TARGET:", target_imgname)
                # Avoid double-stamping
                if ' Reviewed' not in parts:
                    file.write(line + ', Reviewed\n')
                else:
                    file.write(line + '\n')
                updated_any = True
            else:
                file.write(line + '\n')

    # Optional: let yourself know if nothing matched
    # print("Updated:", updated_any)

def Update_Indicator_Status():
    #print("this is get img index return" , Get_Current_Img_Indx())
    #print("Get_filename_from_Indx(current_module, Original_IDX)", Get_filename_from_Indx(Get_Current_Img_Indx(), current_module))
    Original_IDX, Sorted_IDX = Get_Current_Img_Indx()
    Filename = Get_filename_from_Indx(Original_IDX, current_module)
    if Check_If_Image_Reviewed(current_module, Filename):
        indicator.config(text="●", fg="Green", font=("Arial", 32, "bold"))
        #print("this image is reviewed")
        return  
    else: 
        indicator.config(text="●", fg="Red", font=("Arial", 32, "bold"))
        #print("this image is not reviewed")
        return

def Check_If_Image_Reviewed(current_module, target_imgname):
    Original_IDX, Sorted_IDX = Get_Current_Img_Indx()
    #print("Checking if image is reviewed:", target_imgname, "at index", Original_IDX, Sorted_IDX)
    reportlocation = os.path.join(basedir, current_module, "InspectionStatus.txt")
    if not os.path.exists(reportlocation):
        print(f"[DEBUG] Status file missing: {reportlocation}")
        return False

    with open(reportlocation, 'r') as file:
        lines = file.readlines()

    for i in range(len(lines)):
        if i == Sorted_IDX + 1:  # +1 to account for header line
            #print("Checking line:", Sorted_IDX + 1, "Content:", lines[i].strip())
            line = lines[i].strip()
            parts = line.split(',')
            if len(parts) < 2:
                continue
            if parts[1].replace(" ", "") == target_imgname:
                if 'Reviewed' in line:
                    return True

    return False

def retrieve_image_grade(current_module, current_image_index):
    reportlocation = os.path.join(basedir, current_module, "module_report.txt")
    if not os.path.exists(reportlocation):
        return None
    else:
        reportlocation = reportlocation

    # Get the filename for this image
    images = Get_Module_Images(current_module)
    if current_image_index >= len(images):
        return None

    target_image = os.path.basename(images[current_image_index])

    # Scoring weights
    detection_weights = {
        "missing_bond": +1000,
        "tape_in_hole": +1000,
        "debris": + 1000,
        "disfigured_bond": +1000,
        "three_bonds": +0
    }

    overlap_weights = {
        "missing_bond":  +3000,
        "tape_in_hole": +3000,
        "debris": +3000,
        "disfigured_bond": +3000,
        "three_bonds": +0
    }

    score = 0
    current_class = None

    with open(reportlocation, "r") as f:
        lines = f.readlines()

    # --- PASS 1: Count detections for this image ---
    for line in lines:
        line = line.strip()

        # Detect class section headers
        if line.endswith(":") and not line.startswith("Images with"):
            current_class = line.replace(":", "").strip()
            continue

        # Look for detections belonging to this image
        if target_image in line and "[" in line and current_class in detection_weights:
            score += detection_weights[current_class]

    # --- PASS 2: Count overlaps for this image ---
    in_overlap_section = False
    current_overlap_image = None

    for line in lines:
        line = line.rstrip()

        # Detect start of overlap section
        if line.startswith("Images with THREE_BONDS overlaps"):
            in_overlap_section = True
            continue

        if not in_overlap_section:
            continue

        # Detect image header inside overlap section
        if line.endswith("processed.png:"):
            current_overlap_image = line.replace(":", "").strip()
            continue

        # If this is the image we care about, parse overlaps
        if current_overlap_image == target_image and "overlaps with" in line:
            parts = line.split("overlaps with")
            other_class = parts[1].split()[0].strip()

            if other_class in overlap_weights:
                score += overlap_weights[other_class]
        
    # Tertiary score: reverse index
    reverse_index_score = (len(images) - 1) - current_image_index
    score += reverse_index_score


    return score


def Get_Highest_Scored_Image(current_module, line = 1):
    Module_Location = os.path.join(basedir, current_module)
    report_dir = os.path.join(Module_Location, "InspectionStatus.txt")
    if not os.path.exists(report_dir):
        return None
    with open(report_dir, "r") as f:
        lines = f.readlines()
    FileName = lines[line].split(",")[1].strip() 
    #print(" this is lines[2] in get Highest scored Image:", lines[2])
    #print(" this is the image name:", (lines[2].split(","))[1].strip())
    return FileName

def Get_Score_From_Image(current_module, line = 1):
    Module_Location = os.path.join(basedir, current_module)
    report_dir = os.path.join(Module_Location, "InspectionStatus.txt")
    if not os.path.exists(report_dir):
        return None
    with open(report_dir, "r") as f:
        lines = f.readlines()

    if line >= len(lines) - 1:
        #print(f"[DEBUG] Line index {line} out of range for file with {len(lines)} lines.")
        return None
    Score = lines[line+1].split(",")[2].strip() 
    #print(" this is lines[2] in get Highest scored Image:", lines[2])
    #print(" this is the image name:", (lines[2].split(","))[1].strip())
    #print(Score, type(Score))
    return int(Score)

def Get_filename_from_Indx(Indx, current_module):
    reportlocation = os.path.join(basedir, current_module, "InspectionStatus.txt")
    if not os.path.exists(reportlocation):
        return None
    
    with open(reportlocation, "r") as f:
        lines = f.readlines()   

    for line in lines[1:]:  # Skip header
        parts = line.strip().split(",")
        if len(parts) < 4:
            continue
        if int(parts[0].strip()) == Indx:
            return parts[1].strip()  # Return the image name    

def Get_Indx_from_Filename(Filename, current_module):
    reportlocation = os.path.join(basedir, str(current_module), "InspectionStatus.txt")

    if not os.path.exists(reportlocation):
        #print(f"[DEBUG] File not found: {reportlocation}")
        return None

    with open(reportlocation, "r") as f:
        lines = f.readlines()

    for line in lines[1:]:
        parts = line.strip().split(",")
        if len(parts) < 4:
            continue

        
        file_in_list = parts[1].strip()

        #print(parts, file_in_list, Filename)

        if file_in_list == Filename:
            #print(f"[DEBUG] MATCH: {file_in_list} == {Filename}")
            return int(parts[0]), int(parts[3])

        else:
            #print(f"[DEBUG] NO MATCH: {file_in_list} != {Filename}")
            pass

    #print(f"[DEBUG] Filename '{Filename}' not found in InspectionStatus.txt")
    return None



def Build_Inspection_Status(current_module):
    reportlocation = os.path.join(basedir, current_module, "InspectionStatus.txt")

    # Get all images
    images = Get_Module_Images(current_module)

    # Build list of (index, name, grade)
    rows = []
    for idx, imgpath in enumerate(images):
        imgname = os.path.basename(imgpath)
        grade = retrieve_image_grade(current_module, idx)
        rows.append((idx, imgname, grade))

    # Sort by grade (descending = best first)
    sorted_rows = sorted(rows, key=lambda x: x[2], reverse=True)

    # Assign sorted index
    # sorted_index = position in sorted list
    for rank, row in enumerate(sorted_rows):
        original_index, imgname, grade = row
        # Replace tuple with 4‑column version
        sorted_rows[rank] = (original_index, imgname, grade, rank)

    # Write file
    with open(reportlocation, "w") as writefile:
        writefile.write("original_index, image_name, grade, sorted_index\n")
        for row in sorted_rows:
            writefile.write(f"{row[0]}, {row[1]}, {row[2]}, {row[3]}\n")

def Get_Current_Img_Indx():
    #currently returning original index, not sorted index. Need to change this to sorted index for it to work with the next image button properly
    text = top_label.cget("text")          # e.g. "ModuleA — Image 12"
    try:
        # Split on "Image " and take the part after it
        idx_str = text.split("Image ")[1]
        original_IDX  = int(idx_str)
    except (IndexError, ValueError):
        print("cant parse image index from title, returning none")
        return None
    
    #print("this is the original index of the current image:", original_IDX)

    text = top_label.cget("text")          # e.g. "ModuleA — Image 12"
    try:
        # Split on "Image " and take the part after it
        idx_str = text.split(" — ")[0]
        current_module = (idx_str)
    except: 
        print("cant parse module name from title, returning none")
        return None
    

    #print("this is the module of the current image:", current_module)

    reportlocation = os.path.join(basedir, str(current_module), "InspectionStatus.txt")

    if not os.path.exists(reportlocation):
        print(f"[DEBUG] File not found: {reportlocation}")
        return None
    
    #print("this is the report location:", reportlocation)

    with open(reportlocation, "r") as f:
        lines = f.readlines()

    for line in lines[1:]:
        parts = line.strip().split(",")
        if parts[0].strip() == str(original_IDX):
            return int(parts[0].strip()), int(parts[3].strip())  # Return the image name and sorted index
    

    

    





def Update_Images(current_module, img_indx):
    #global current_image_index
    #current_image_index = img_indx

    #print("Images Debug: ", current_module, img_indx, Get_Score_From_Image(current_module, img_indx), Get_filename_from_Indx(img_indx, current_module))

    selected_module = current_module
    images = Get_Module_Images(selected_module)
    Img_Name = Get_Highest_Scored_Image(selected_module)

    #print(img_indx, type(img_indx))

    if images:
        new_image = tk.PhotoImage(file=images[int(img_indx)])
        img_label.config(image=new_image)
        img_label.image = new_image

    Update_Title(Img_Name)   # <-- update title card


def Reverse_Module_Position(images, focusimg):
    for photo in images:
        if photo == focusimg:
            return images.index(photo)

def Get_Module_Names():
    module_names = []

    if not os.path.exists(report_dir):
        raise FileNotFoundError(f"REPORT_DIR does not exist: {report_dir}")

    for folder in os.listdir(report_dir):
        module_path = os.path.join(report_dir, folder)
        if os.path.isdir(module_path):
            module_names.append(folder)

    return module_names

def Get_Module_Images(module_name):
    images = []
    module_path = os.path.join(report_dir, module_name)
    if os.path.exists(module_path):
        for file in os.listdir(module_path):
            if file.endswith(".png"):
                images.append(os.path.join(module_path, file))
    return images

def Get_Scored_Module_Images(module_name):
    images = Get_Module_Images(module_name)
    scored_images = []
    for idx, img in enumerate(images):
        grade = retrieve_image_grade(module_name, idx)
        scored_images.append((img, grade))
    return scored_images


#prelaucnh check
List = Get_Module_Names()
for module in List:
    if not os.path.exists(os.path.join(basedir, module, "InspectionStatus.txt")):
        #print(f"[DEBUG] Missing InspectionStatus.txt for module: {module}")
        Build_Inspection_Status(module)

root = tk.Tk()
root.geometry("1000x800")
current_module = Get_Module_Names()[0]  # Start with the first module
current_image_index = 0
# --- Somewhere around line 230 in TK_Reviewer.py ---
status = read_first_module_status(current_module)

if status and status["image_name"]:
    # Construct the full path to the image using the name from the file
    first_image = os.path.join(basedir, current_module, status["image_name"])
else:
    # Fallback if no status exists yet: use a default placeholder or the first image in the folder
    images = Get_Module_Images(current_module)
    first_image = images[0] if images else "path/to/a/default_placeholder.png"
# Now Tkinter won't crash because first_image will always point to something real
Img_Focus = tk.PhotoImage(file=first_image)


# Create a 3×3 grid with equal weight
for r in range(3):
    root.rowconfigure(r, weight=1)
for c in range(3):
    root.columnconfigure(c, weight=1)

# Load your image
Img_Focus = tk.PhotoImage(file=first_image)

# --- Surrounding labels ---
labels = {
    (0,0): "Top Left",
    (2,0): "Bottom Left",
    (2,1): "Bottom Center"
}

# --- TOP CENTER: Label that will show the selected module ---
title_font = font.Font(size=20, weight="bold")
top_label = tk.Label(root, text="Select a Module", font=title_font, bg="#d0d0ff")
top_label.grid(row=0, column=1, sticky="nsew")
filename_label = tk.Label(root, text="", font=("Arial", 14), bg="#d0d0ff")
filename_label.grid(row=0, column=1, sticky="s")   # stick to bottom of the top cell

Failure_Percentile_Label = tk.Label(root, text="", font=("Arial", 14), bg="#d0d0ff")
Failure_Percentile_Label.grid(row=0, column=2, sticky="n")



# --- LEFT SIDE: Listbox with module names ---
listbox = tk.Listbox(root)
listbox.grid(row=1, column=0, sticky="nsew")

# Populate the listbox with module names
ModList = Get_Module_Names()
for module in ModList:
    listbox.insert(tk.END, module)

def on_Mark_Reviewed(event):
    Original_IDX, Sorted_IDX = Get_Current_Img_Indx()
    current_image_name = Get_Highest_Scored_Image(current_module, Sorted_IDX+1)
    #print("Marking current image as reviewed...", current_module, current_image_name)
    Stamp_Image_Complete(current_module, current_image_name)
    Update_Indicator_Status()

    #Build_Inspection_Status(current_module)    

def Mark_All_Reviewed(event):
    Original_IDX, Sorted_IDX = Get_Current_Img_Indx()
    current_image_name = Get_Highest_Scored_Image(current_module, Sorted_IDX+1)

    #print("Marking current image as reviewed...", current_module, current_image_name)
    Percentile = Check_Module_Percentage()
    if Percentile is not None and Percentile >= 90:
        print(f"Marking All Images as Reviewed... Percentile is 90% or above")

        Stamp_All_Complete(current_module, current_image_name)
    else:
        print("Mark All Locked... Percentile is below 90%")
    Update_Indicator_Status()

    #Build_Inspection_Status(current_module) 

def Check_Module_Percentage():
    #currently returning original index, not sorted index. Need to change this to sorted index for it to work with the next image button properly
    text = Failure_Percentile_Label.cget("text")          # e.g. "ModuleA — Image 12"
    try:
        text.split("Failure Percentile: ")[1].replace("%", "")
        percentile = float(text.split("Failure Percentile: ")[1].replace("%", ""))
        return percentile
    except (IndexError, ValueError):
        print("cant parse percentile from label, returning none")
        return None


def on_Next_Image_Select(event):
    images = Get_Module_Images(current_module)
    original_IDX, Sorted_IDX = Get_Current_Img_Indx()
    current_image_index = Sorted_IDX
    #print(f"Clicked: {current_image_index}")

    #print("DEBUG CURRENT IMAGE INDEX", current_image_index, type(current_image_index))
    #print("on 371 currentmodule = ", current_module, "Img_Name = ", Get_Highest_Scored_Image(current_module, current_image_index+1))
    #Original_IDX, Graded_IDX = Get_Indx_from_Filename(Get_Highest_Scored_Image(current_module, current_image_index+1), current_module)
    #current_image_index = Graded_IDX
    #if current_image_index >= len(images):
    #    current_image_index = 0  # Loop back to the first image
    #try:
    current_image_index + 2
    #print("this is the index of the next image:", current_image_index + 2)
    #except Exception as e:
    #    #print(f"[DEBUG] Error: {e}")

    if type(current_image_index) != int:
        #print(f"[DEBUG] current_image_index is not an integer: {current_image_index}")
        return

    Update_Images(current_module, current_image_index+2)
    New_Update_Failure_Percentile(Get_Highest_Scored_Image(current_module, current_image_index+2))
    Update_Title(Get_Highest_Scored_Image(current_module, current_image_index+2))
    Update_Indicator_Status()
    #print(f"Updated: {current_image_index}")

def on_module_select(event):
    global current_module, current_image_index
    current_image_index  = 0  # Reset to first image when module changes

    selection = listbox.curselection()
    if not selection:
        return

    current_module = listbox.get(selection[0])
    Current_Img_Name = Get_Highest_Scored_Image(current_module, 1)
    #print("this is current img name (after click )", Current_Img_Name)

    Update_Title(Current_Img_Name)
    Update_Images(current_module, current_image_index)
    New_Update_Failure_Percentile(Current_Img_Name) 
    Update_Indicator_Status()

def Update_Title(Img_Name):
    if current_module is None:
        return

    images = Get_Module_Images(current_module)
    #print(current_module, current_image_index)
    #print("This is Filename (line 334):", images[current_image_index].replace(basedir, "").replace(current_module, "").replace(f"\\\_", ""))
    filename = os.path.basename(images[current_image_index])

    #print(f"[DEBUG] Updating title: Module={current_module}, Image={filename}, Img_Name={Img_Name}")

    #print("on 409 currentmodule = ", current_module, "Img_Name = ", Img_Name)
    Original_IDX, Graded_IDX = Get_Indx_from_Filename(Img_Name, current_module)

    top_label.config(
        text=f"{current_module} — Image {Original_IDX}"
    )

    imgName = Get_filename_from_Indx(Img_Name, current_module)
    filename_label.config(text=Img_Name)

"""def Update_Failure_Percentile(Img_Name):
    if current_module is None:
        return
    isLess = 0

    images = Get_Module_Images(current_module)
    
    #print("on 424 currentmodule = ", current_module, "Img_Name = ", Img_Name)
    Original_IDX, Graded_IDX = Get_Indx_from_Filename(Img_Name, current_module)  
    #print("this is the image index of the focus image:", Original_IDX)

    #print("control score inputs, " , Graded_IDX, current_module)
    Control_Score = Get_Score_From_Image(current_module, Graded_IDX)

    Denominator = 0

    #print("Debug:", len(images), "images found for module", current_module)
    for i in range(len(images)-1):
        if i >= len(images):
            print(f"[DEBUG] Image index {i} out of range for images list with length {len(images)}")
        else:#print (f"Getidx from filename inputs:  {current_module}{i+1}...")
            Variable_Score = Get_Score_From_Image(current_module, i+1)
            if Variable_Score < Control_Score:
                isLess += 1
        
    #print (f"{isLess} is the number of modules that are less than the focus image score of {Control_Score}")

    # Calculate percentile
    total_images = len(images)
    
    percentile = 100 - (isLess / total_images if total_images > 0 else 0) * 100   

    #print("this is the percentile:", percentile,"=", isLess, "over", total_images)

    Failure_Percentile_Label.config(
        text=f"Failure Percentile: {percentile:.1f}%"
    )
    #print("this is is less:", isLess)
"""

def New_Update_Failure_Percentile(Img_Name):
    if current_module is None:
        return
    isLess = 0

    images = Get_Module_Images(current_module)
    
    #print("on 424 currentmodule = ", current_module, "Img_Name = ", Img_Name)
    Original_IDX, Graded_IDX = Get_Indx_from_Filename(Img_Name, current_module)  
    #print("this is the image index of the focus image:", Original_IDX)

    #print("control score inputs, " , Graded_IDX, current_module)
    Control_Score = Get_Score_From_Image(current_module, Graded_IDX)


    Denominator = 0
    Numerator = 0

    #print("Debug:", len(images), "images found for module", current_module)
    for i in range(len(images)-1):
        if i >= len(images):
            print(f"[DEBUG] Image index {i} out of range for images list with length {len(images)}")
        else:#print (f"Getidx from filename inputs:  {current_module}{i+1}...")
            Denominator += Get_Score_From_Image(current_module, i+1)

            if i <= Graded_IDX:
                Numerator += Get_Score_From_Image(current_module, i+1)


        
    print("This is denominator: ", Denominator) 
    print("this is numerator: ", Numerator)   
    #print (f"{isLess} is the number of modules that are less than the focus image score of {Control_Score}")

    # Calculate percentile
    total_images = len(images)
    
    percentile = (Numerator / Denominator if Denominator > 0 else 0) * 100   

    #print("this is the percentile:", percentile,"=", isLess, "over", total_images)

    Failure_Percentile_Label.config(
        text=f"Failure Percentile: {percentile:.1f}%"
    )
    print("this is is percentile:", percentile)



listbox.bind("<<ListboxSelect>>", on_module_select)    

# --- RIGHT SIDE: Button ---
btn_right = tk.Button(root, text="NEXT IMAGE")
btn_right.grid(row=1, column=2, sticky="nsew")
btn_right.bind("<Button-1>", on_Next_Image_Select)

# Create a container frame
right_container = tk.Frame(root)
right_container.grid(row=2, column=2, sticky="nsew")
right_container.grid_rowconfigure(0, weight=1)
right_container.grid_columnconfigure(0, weight=1)


# Button
btm_btn_right = tk.Button(right_container, text="Mark as Reviewed")
btm_btn_right.grid(row=0, column=0, sticky="nsew")
btm_btn_right.bind("<Button-1>", on_Mark_Reviewed)

# Mark All Button
Mark_All_Button = tk.Button(right_container, text="Mark All Reviewed")
Mark_All_Button.grid(row=0, column=1, sticky="nsew")
Mark_All_Button.bind("<Button-1>", Mark_All_Reviewed)



#indicator Label
Indicator_Label = tk.Label(right_container, text="Review Status:", font=("Arial", 14))
Indicator_Label.grid(row=1, column=0, padx=5, sticky="e")

# Indicator ITSELF
indicator = tk.Label(right_container, text="●", fg="red")
indicator.grid(row=1, column=1, padx=5)


for (r, c), text in labels.items():
    tk.Label(root, text=text, bg="#e0e0e0").grid(row=r, column=c, sticky="nsew")

# --- Center image ---
img_label = tk.Label(root, image=Img_Focus)
img_label.image = Img_Focus
img_label.grid(row=1, column=1, sticky="nsew")

Failure_Percentile_Label.grid(row=0, column=2, sticky="n")

root.mainloop()