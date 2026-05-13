import os
import glob
from collections import Counter

LABEL_DIR = r"C:\TensorFlow_Datasets\Datasets\Dataset_3_YOLO\labels\train"

def count_samples(label_dir):
    class_counts = Counter()
    file_count = 0

    for file in glob.glob(os.path.join(label_dir, "**/*.txt"), recursive=True):
        file_count += 1
        with open(file, "r") as f:
            for line in f:
                parts = line.strip().split()
                if not parts:
                    continue
                try:
                    cls = int(parts[0])
                    class_counts[cls] += 1
                except ValueError:
                    print(f"Warning: malformed line in {file}: {line}")

    print("\n=== CLASS SAMPLE COUNT ===")
    print(f"Label files scanned: {file_count}\n")

    for cls_id in sorted(class_counts.keys()):
        print(f"Class {cls_id}: {class_counts[cls_id]} samples")

    # Detect unexpected classes
    expected = {0,1,2,3,4}
    found = set(class_counts.keys())
    unexpected = found - expected

    if unexpected:
        print("\n⚠ WARNING: Unexpected class IDs found:", unexpected)
    else:
        print("\nAll class IDs are within expected range 0–4.")

    return class_counts

count_samples(LABEL_DIR)
