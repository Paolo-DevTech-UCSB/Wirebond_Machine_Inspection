import os
from ultralytics import YOLO
from collections import defaultdict

# ============================================================
# CONFIGURATION
# ============================================================

MODEL_PATH = r"C:\Users\hep\Documents\GitHub Forks\Wirebond_Inspector\Wirebond_Machine_Inspection\runs\detect\train-14\weights\best.pt"
DEFAULT_FOLDER = r"C:\Users\hep\Desktop\Wirebond_Inspector\Processed Photos\Default"
OUTPUT_ROOT = r"C:\Users\hep\Desktop\Wirebond_Inspector\Module_Reports"

# ============================================================
# RUN YOLO ON A SINGLE MODULE
# ============================================================

def evaluate_module(module_id):
    
    model = YOLO(MODEL_PATH)

    labelstudio_to_yolo = {
        2: 1,  # debris
        3: 3,  # tape_in_hole
        4: 0,  # three_bonds
        5: 4,  # disfigured_bond
        6: 2   # missing_bond
    }



    # Find all images for this module
    image_paths = []
    for f in os.listdir(DEFAULT_FOLDER):
        if f.lower().endswith((".png", ".jpg", ".jpeg")):
            if f.startswith(module_id):  # first 15 chars match
                image_paths.append(os.path.join(DEFAULT_FOLDER, f))

    if not image_paths:
        print(f"No images found for module {module_id}")
        return

    # Output folder
    output_path = os.path.join(OUTPUT_ROOT, f"Module_{module_id}")
    os.makedirs(output_path, exist_ok=True)

    print(f"\n=== Evaluating Module {module_id} ===")
    print(f"Images found: {len(image_paths)}")

    class_counts = defaultdict(int)
    per_image = {}

    for img_path in image_paths:
        img_name = os.path.basename(img_path)

        results = model(img_path)

        # Save annotated image
        results[0].save(os.path.join(output_path, img_name))

        detections = results[0].boxes
        per_image[img_name] = len(detections)

        for box in detections:
            raw_id = int(box.cls[0])
            cls_id = labelstudio_to_yolo.get(raw_id, raw_id)
            class_counts[cls_id] += 1

        print(f"  {img_name}: {len(detections)} detections")

    print("\nImages per class:")
    names = model.names

    # Build reverse index: class → list of images
    print("\nImages per class:")
    names = model.names

    class_to_images = defaultdict(list)

    for img_path in image_paths:
        img_name = os.path.basename(img_path)
        results = model(img_path)

        for box in results[0].boxes:
            raw_id = int(box.cls[0])
            cls_id = labelstudio_to_yolo.get(raw_id, raw_id)
            class_to_images[cls_id].append(img_name)

    for cls_id, images in class_to_images.items():
        class_name = names.get(cls_id, f"Class_{cls_id}")
        print(f"  {class_name}:")
        for img in images:
            print(f"    - {img}")



    # Summary
    print("\n--- MODULE REPORT ---")
    print(f"Module ID: {module_id}")
    print(f"Total images: {len(image_paths)}")
    print(f"Total detections: {sum(class_counts.values())}")

    print("\nDetections per class:")
    names = model.names  # class ID → class name
    for cls_id, count in class_counts.items():
        class_name = names.get(cls_id, f"Class_{cls_id}")
        print(f"  {class_name}: {count}")

    print("\nAnnotated images saved to:")
    print(output_path)

    print("\n--- END OF REPORT ---")



# ============================================================
# RUN IT
# ============================================================

if __name__ == "__main__":
    # Example: module ID = first 15 characters of filename
    evaluate_module("320MHF2TDSB0091")
