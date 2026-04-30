import os
import shutil
import re

# === CONFIG ===
YOLO_ROOT = r"C:\TensorFlow_Datasets\Datasets\Dataset 1\project-1-at-2026-04-21-16-30-40aa3357"
TF_OUTPUT = r"C:\TensorFlow_Datasets\Datasets\Dataset 1\TF_Converted"

# Source folder of ALL processed images
ORIGINAL_IMAGES_DIR = r"C:\Users\hep\Desktop\Wirebond_Inspector\Processed Photos\Default"

# Class names in correct order
CLASS_NAMES = [
    "no_defect",
    "debris",
    "disfigured_bond",
    "lifted_bond_foot",
    "missing_bond",
    "tape_in_hole"
]

IMG_EXTS = [".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"]

images_dir = os.path.join(YOLO_ROOT, "images")
labels_dir = os.path.join(YOLO_ROOT, "labels")

def strip_uuid(filename):
    """Remove UUID prefix before the first dash."""
    if "-" in filename:
        return filename.split("-", 1)[1]
    return filename

# ------------------------------------------------------------
# 0. CLEAN TF_Converted COMPLETELY
# ------------------------------------------------------------
if os.path.exists(TF_OUTPUT):
    shutil.rmtree(TF_OUTPUT)

os.makedirs(TF_OUTPUT, exist_ok=True)

# Create class folders
for cname in CLASS_NAMES:
    os.makedirs(os.path.join(TF_OUTPUT, cname), exist_ok=True)

# ------------------------------------------------------------
# 1. Build lookup table for YOLO images
# ------------------------------------------------------------
image_lookup = {}

for img in os.listdir(images_dir):
    lower = img.lower()
    if any(lower.endswith(ext) for ext in IMG_EXTS):
        stripped = strip_uuid(img)
        image_lookup[stripped] = img  # stripped → actual filename

# ------------------------------------------------------------
# 2. Convert YOLO defect classes ONLY
# ------------------------------------------------------------
missing_images = []

for label_file in os.listdir(labels_dir):
    if not label_file.endswith(".txt"):
        continue

    stripped_label = strip_uuid(label_file)
    base = os.path.splitext(stripped_label)[0]

    matched_image = None
    for ext in IMG_EXTS:
        candidate = base + ext
        if candidate in image_lookup:
            matched_image = image_lookup[candidate]
            break

    if matched_image is None:
        missing_images.append(base)
        continue

    with open(os.path.join(labels_dir, label_file), "r") as f:
        first_line = f.readline().strip()

    # Empty label = no_defect → handled later in Step 3
    if not first_line:
        continue

    yolo_class = int(first_line.split()[0])
    tf_class_name = CLASS_NAMES[yolo_class + 1]  # shift by +1

    shutil.copy(
        os.path.join(images_dir, matched_image),
        os.path.join(TF_OUTPUT, tf_class_name)
    )

print("Conversion complete!")
print(f"TensorFlow dataset created at: {TF_OUTPUT}")

if missing_images:
    print("\nWARNING: These labels had no matching images:")
    for m in missing_images[:20]:
        print("  ", m)
    print(f"...and {len(missing_images)} total missing.")
else:
    print("All YOLO images matched successfully!")

# ============================================================
# STEP 3 — AUTO‑EXTRACT NO‑DEFECT IMAGES (FINAL CLEAN VERSION)
# ============================================================

print("\nExtracting no‑defect images...")

module_regex = re.compile(r"(320MHF2[A-Z]{4}\d{4})")

# ------------------------------------------------------------
# 1. Extract valid YOLO modules (from label filenames)
# ------------------------------------------------------------
valid_modules = set()

for label_file in os.listdir(labels_dir):
    if not label_file.endswith(".txt"):
        continue

    stripped = strip_uuid(label_file)
    base = os.path.splitext(stripped)[0]

    m = module_regex.match(base)
    if m:
        valid_modules.add(m.group(1))

print("\n=== YOLO MODULES DETECTED ===")
for m in sorted(valid_modules):
    print("YOLO:", m)
print(f"Total YOLO modules: {len(valid_modules)}")

# ------------------------------------------------------------
# 2. Build label lookup
# ------------------------------------------------------------
label_map = {}
for label_file in os.listdir(labels_dir):
    if label_file.endswith(".txt"):
        stripped = strip_uuid(label_file)
        base = os.path.splitext(stripped)[0]
        label_map[base] = os.path.join(labels_dir, label_file)

# ------------------------------------------------------------
# 3. Process Default images → copy no-defect into TF_Converted/no_defect
# ------------------------------------------------------------
added = 0
skipped_defect = 0
skipped_wrong_module = 0

default_modules = set()

for img in os.listdir(ORIGINAL_IMAGES_DIR):
    if not img.lower().endswith(tuple(IMG_EXTS)):
        continue

    stripped = strip_uuid(img)
    base = os.path.splitext(stripped)[0]

    # Extract module name
    m = module_regex.match(base)
    if not m:
        skipped_wrong_module += 1
        continue

    module_name = m.group(1)
    default_modules.add(module_name)

    # Skip modules not in YOLO
    if module_name not in valid_modules:
        skipped_wrong_module += 1
        continue

    # Check label
    label_path = label_map.get(base, None)

    if label_path:
        if os.path.getsize(label_path) > 0:
            skipped_defect += 1
            continue
        # else: empty label → no-defect

    # Copy valid no-defect image into TF dataset
    shutil.copy(
        os.path.join(ORIGINAL_IMAGES_DIR, img),
        os.path.join(TF_OUTPUT, "no_defect", img)
    )
    added += 1

# ------------------------------------------------------------
# 4. Diagnostics
# ------------------------------------------------------------
print("\n=== DEFAULT MODULES DETECTED ===")
for m in sorted(default_modules):
    print("DEFAULT:", m)
print(f"Total Default modules: {len(default_modules)}")

extra = default_modules - valid_modules
missing = valid_modules - default_modules

print("\n=== MODULES IN DEFAULT BUT NOT IN YOLO ===")
for m in sorted(extra):
    print("EXTRA:", m)
print(f"Count extra: {len(extra)}")

print("\n=== MODULES IN YOLO BUT NOT IN DEFAULT ===")
for m in sorted(missing):
    print("MISSING:", m)
print(f"Count missing: {len(missing)}")

# ------------------------------------------------------------
# 5. Summary
# ------------------------------------------------------------
print(f"\nAdded {added} new no‑defect images.")
print(f"Skipped {skipped_defect} defect images.")
print(f"Skipped {skipped_wrong_module} images from modules NOT in YOLO dataset.")
print("No‑defect extraction complete!")

# MOVE entire folder into C:\TensorFlow Datasets