import os
import shutil

# === CONFIG ===
SOURCE_DIR = r"C:\TensorFlow_Datasets\Source"
DEFAULT_DIR = r"C:\Users\hep\Desktop\Wirebond_Inspector\Processed Photos\Default"

IMG_EXTS = (".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp")

# Normalize filenames by stripping UUIDs
def strip_uuid(filename):
    if "-" in filename:
        return filename.split("-", 1)[1]
    return filename

# ------------------------------------------------------------
# 1. Build list of images already in SOURCE
# ------------------------------------------------------------
source_files = set()

for f in os.listdir(SOURCE_DIR):
    if f.lower().endswith(IMG_EXTS):
        source_files.add(strip_uuid(f))

# ------------------------------------------------------------
# 2. Scan DEFAULT and find missing images
# ------------------------------------------------------------
missing = []

for f in os.listdir(DEFAULT_DIR):
    if not f.lower().endswith(IMG_EXTS):
        continue

    stripped = strip_uuid(f)

    if stripped not in source_files:
        missing.append(f)

# ------------------------------------------------------------
# 3. Move missing images into SOURCE
# ------------------------------------------------------------
moved = 0

for f in missing:
    src_path = os.path.join(DEFAULT_DIR, f)
    dst_path = os.path.join(SOURCE_DIR, f)

    shutil.copy(src_path, dst_path)
    moved += 1

# ------------------------------------------------------------
# 4. Summary
# ------------------------------------------------------------
print(f"Total images in SOURCE: {len(source_files)}")
print(f"Images in DEFAULT not in SOURCE: {len(missing)}")
print(f"Moved {moved} images into SOURCE.")
print("Sync complete.")


