import os
from ultralytics import YOLO
from collections import defaultdict
from preprocess.Folder_Builder import get_module_paths
from Folder_to_Report_config import CONFIG

from Boundry_Matching import main as boundary_matcher

MODEL_PATH = r"C:\Users\hep\Documents\GitHub Forks\Wirebond_Inspector\Wirebond_Machine_Inspection\runs\detect\train-5\weights\best.pt"

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

    CLASS_NAMES = {
        0: "debris",
        1: "disfigured_bond",
        2: "missing_bond",
        3: "tape_in_hole",
        4: "three_bonds"
    }

    class_counts = defaultdict(int)
    class_to_images = defaultdict(list)
    detections_by_image = {}

    for img_path in image_paths:
        img_name = os.path.basename(img_path)
        results = model(img_path)

        # Save annotated image
        results[0].save(os.path.join(report_root, img_name))

        detections = results[0].boxes
        det_list = []

        for box in detections:
            cls_id = int(box.cls[0])
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            coords = [round(x1, 2), round(y1, 2), round(x2, 2), round(y2, 2)]

            det_list.append((cls_id, coords))
            class_counts[cls_id] += 1
            class_to_images[cls_id].append((img_name, coords))

        detections_by_image[img_name] = det_list

        print(f"  {img_name}: {len(detections)} detections")

    # Run overlap detection
    overlap_report = boundary_matcher(detections_by_image)

    # ------------------------------------------------------------
    # WRITE TEXT REPORT
    # ------------------------------------------------------------
    report_path = os.path.join(report_root, "module_report.txt")

    with open(report_path, "w") as f:
        f.write("MODULE REPORT\n")
        f.write(f"Module ID: {module_id}\n")
        f.write(f"Total images: {len(image_paths)}\n")
        f.write(f"Total detections: {sum(class_counts.values())}\n\n")

        f.write("Class Counts:\n")
        for cls_id, name in CLASS_NAMES.items():
            f.write(f"  {name}: {class_counts.get(cls_id, 0)}\n")

        f.write("\nImages with detections:\n")
        for cls_id, name in CLASS_NAMES.items():
            f.write(f"\n{name}:\n")
            entries = class_to_images.get(cls_id, [])

            if entries:
                grouped = defaultdict(list)
                for img, coords in entries:
                    grouped[img].append(coords)

                for img, coords_list in grouped.items():
                    f.write(f"  {img}")
                    for coords in coords_list:
                        f.write(f" [{coords[0]}, {coords[1]}, {coords[2]}, {coords[3]}]")
                    f.write("\n")
            else:
                f.write("  (none)\n")

        # ------------------------------------------------------------
        # THREE_BONDS OVERLAP SECTION
        # ------------------------------------------------------------
        f.write("\nImages with THREE_BONDS overlaps:\n")

        if overlap_report:
            for img, overlaps in overlap_report.items():
                f.write(f"\n{img}:\n")
                for tb, (cls_id, obox) in overlaps:
                    f.write(
                        f"  three_bonds {tb} overlaps with "
                        f"{CLASS_NAMES[cls_id]} {obox}\n"
                    )
        else:
            f.write("  (none)\n")

    print(f"Text report saved to: {report_path}")

    print("\n--- MODULE REPORT ---")
    print(f"Module ID: {module_id}")
    print(f"Annotated images saved to: {report_root}")
    print("--- END OF REPORT ---")
