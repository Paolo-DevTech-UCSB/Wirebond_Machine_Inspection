
import os
import random
import urllib.parse
from shutil import copy2

# ============================================================
# CONFIGURATION
# ============================================================

YOLO_ROOT = r"C:\TensorFlow_Datasets\Datasets\Dataset_3_YOLO\project-4-at-2026-05-19-17-16-4f71207f"
SOURCE_IMAGES = r"C:\TensorFlow_Datasets\Source"

OUTPUT = r"C:\TensorFlow_Datasets\Datasets\Dataset_3_YOLO"

TRAIN_SPLIT = 0.95

# ============================================================
# DIRECTORY SETUP
# ============================================================

labels_dir = os.path.join(YOLO_ROOT, "labels")

os.makedirs(os.path.join(OUTPUT, "images", "train"), exist_ok=True)
os.makedirs(os.path.join(OUTPUT, "images", "val"), exist_ok=True)
os.makedirs(os.path.join(OUTPUT, "labels", "train"), exist_ok=True)
os.makedirs(os.path.join(OUTPUT, "labels", "val"), exist_ok=True)

# ============================================================
# GATHER IMAGE/LABEL PAIRS
# ============================================================

pairs = []

for label_file in os.listdir(labels_dir):
    if not label_file.endswith(".txt"):
        continue

    base = os.path.splitext(label_file)[0]
    base = urllib.parse.unquote(base)

    if "__" in base:
        base = base.split("__", 1)[1]

    base = os.path.basename(base)

    img_path = None
    # Try exact match first
    for ext in [".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"]:
        candidate = os.path.join(SOURCE_IMAGES, base + ext)
        if os.path.exists(candidate):
            img_path = candidate
            break

    # Try "_processed" match
    if img_path is None:
        for ext in [".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"]:
            candidate = os.path.join(SOURCE_IMAGES, base + "_processed" + ext)
            if os.path.exists(candidate):
                img_path = candidate
                break


    if img_path is None:
        print("WARNING: No image for label:", label_file)
        continue

    pairs.append((img_path, os.path.join(labels_dir, label_file)))

random.shuffle(pairs)

split_index = int(len(pairs) * TRAIN_SPLIT)
train_pairs = pairs[:split_index]
val_pairs = pairs[split_index:]

print(f"Total images: {len(pairs)}")
print(f"Train: {len(train_pairs)}")
print(f"Val: {len(val_pairs)}")

# ============================================================
# COPY INTO YOLO STRUCTURE
# ============================================================

def copy_pairs(pairs, split):
    for img_path, label_path in pairs:
        copy2(img_path, os.path.join(OUTPUT, "images", split))
        copy2(label_path, os.path.join(OUTPUT, "labels", split))

copy_pairs(train_pairs, "train")
copy_pairs(val_pairs, "val")

print("YOLO dataset built successfully!")
print("Output folder:", OUTPUT)
