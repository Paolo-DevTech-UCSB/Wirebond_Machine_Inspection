import os
from ultralytics import YOLO
from collections import defaultdict
from preprocess.Folder_Builder import get_module_paths
from Folder_to_Report_config import CONFIG

MODEL_PATH = r"C:\Users\hep\Documents\GitHub Forks\Wirebond_Inspector\Wirebond_Machine_Inspection\runs\detect\train-14\weights\best.pt"

def evaluate_module(module_id):

    model = YOLO(MODEL_PATH)

    module_input, module_output = get_module_paths(module_id)
    default_folder = module_output["Default"]

    report_root = os.path.join(
        CONFIG["BASE_DIR"],
        CONFIG["REPORT_DIR"],
        module_id
    )
    os.makedirs(report_root, exist_ok=True)

    image_paths = [
        os.path.join(default_folder, f)
        for f in os.listdir(default_folder)
        if f.lower().endswith((".png", ".jpg", ".jpeg"))
    ]

    if not image_paths:
        print(f"No Default images found for module {module_id}")
        return

    print(f"\n=== Evaluating Module {module_id} ===")
    print(f"Images found: {len(image_paths)}")

    class_counts = defaultdict(int)
    class_to_images = defaultdict(list)

    for img_path in image_paths:
        img_name = os.path.basename(img_path)

        results = model(img_path)

        results[0].names = {
            0: "three_bonds",
            1: "debris",
            2: "missing_bond",
            3: "tape_in_hole",
            4: "disfigured_bond"
        }

        results[0].save(os.path.join(report_root, img_name))



        detections = results[0].boxes

        for box in detections:
            cls_id = int(box.cls[0])
            class_counts[cls_id] += 1
            class_to_images[cls_id].append(img_name)

        print(f"  {img_name}: {len(detections)} detections")

    print("\n--- MODULE REPORT ---")
    print(f"Module ID: {module_id}")
    print(f"Annotated images saved to: {report_root}")
    print("--- END OF REPORT ---")
