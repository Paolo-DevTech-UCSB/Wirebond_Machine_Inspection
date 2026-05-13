import os
from ultralytics import YOLO
from collections import defaultdict

# ============================================================
# CONFIGURATION
# ============================================================

MODEL_PATH = r"C:\Users\hep\Documents\GitHub Forks\Wirebond_Inspector\Wirebond_Machine_Inspection\runs\detect\train-14\weights\best.ptt"
DEFAULT_FOLDER = r"C:\Users\hep\Desktop\Wirebond_Inspector\Processed Photos\Default"
OUTPUT_ROOT = r"C:\Users\hep\Desktop\Wirebond_Inspector\Module_Reports"

# ============================================================
# HELPER: Extract module ID from filename
# ============================================================

def get_module_id(filename):
    # Module ID = first 15 characters of the filename (before extension)
    base = os.path.splitext(filename)[0]
    return base[:15]  # first 15 chars

# ============================================================
# MAIN TESTING FUNCTION
# ============================================================

def test_module(model, module_id, image_paths, output_path):
    os.makedirs(output_path, exist_ok=True)

    labelstudio_to_yolo = {
        2: 1,  # debris
        3: 3,  # tape_in_hole
        4: 0,  # three_bonds
        5: 4,  # disfigured_bond
        6: 2   # missing_bond
    }

    class_counts = defaultdict(int)
    image_results = {}

    print(f"\n=== Testing Module {module_id} ===")
    print(f"Images: {len(image_paths)}")

    for img_path in image_paths:
        img_name = os.path.basename(img_path)

        results = model(img_path)

        # Save annotated image
        save_path = os.path.join(output_path, img_name)
        results[0].save(save_path)

        detections = results[0].boxes
        image_results[img_name] = len(detections)

        for box in detections:
            raw_id = int(box.cls[0])
            cls_id = labelstudio_to_yolo.get(raw_id, raw_id)
            class_counts[cls_id] += 1

        print(f"  {img_name}: {len(detections)} detections")

    # Summary
    print("\n--- Module Summary ---")
    print(f"Module: {module_id}")
    print(f"Total images: {len(image_paths)}")
    print(f"Total detections: {sum(class_counts.values())}")

    return {
        "module": module_id,
        "images": len(image_paths),
        "total_detections": sum(class_counts.values()),
        "class_counts": dict(class_counts),
        "image_results": image_results
    }

# ============================================================
# RUN ON ALL MODULES
# ============================================================

def main():
    model = YOLO(MODEL_PATH)

    # Group images by module ID
    modules = defaultdict(list)

    for f in os.listdir(DEFAULT_FOLDER):
        if f.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff")):
            module_id = get_module_id(f)
            modules[module_id].append(os.path.join(DEFAULT_FOLDER, f))

    print(f"Found {len(modules)} modules.")

    master_report = []

    for module_id, image_paths in modules.items():
        output_path = os.path.join(OUTPUT_ROOT, f"Module_{module_id}")
        report = test_module(model, module_id, image_paths, output_path)
        master_report.append(report)

    print("\n================ MASTER REPORT ================")
    for r in master_report:
        print(f"Module {r['module']}: {r['total_detections']} detections across {r['images']} images")

    print("\nAnnotated results saved to:", OUTPUT_ROOT)
    print("===============================================")


if __name__ == "__main__":
    main()
