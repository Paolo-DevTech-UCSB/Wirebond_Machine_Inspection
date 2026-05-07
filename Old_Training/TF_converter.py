import os
import io
import random
import urllib.parse
import tensorflow as tf
from PIL import Image
from shutil import copy2

# ============================================================
# CONFIGURATION
# ============================================================

# Path to your Label Studio YOLO export
YOLO_ROOT = r"C:\TensorFlow_Datasets\Datasets\Dataset 2c\project-4-at-2026-05-04-20-24-73cd1ce2"

# Output TFRecord dataset folder
TF_OUTPUT = r"C:\TensorFlow_Datasets\Datasets\Dataset 2c\TF_Converted"

# Class list (MUST match Label Studio order)
CLASS_NAMES = [
    "three_bonds",
    "debris",
    "missing_bond",
    "tape_in_hole",
    "disfigured_bond"
]

# Train/Val split
TRAIN_SPLIT = 0.90

# ============================================================
# DIRECTORY SETUP
# ============================================================

# Images do NOT live in the YOLO export folder.
# They live in the original source folder used by Label Studio.
images_dir = r"C:\TensorFlow_Datasets\Source"

labels_dir = os.path.join(YOLO_ROOT, "labels")

os.makedirs(os.path.join(TF_OUTPUT, "images", "train"), exist_ok=True)
os.makedirs(os.path.join(TF_OUTPUT, "images", "val"), exist_ok=True)
os.makedirs(os.path.join(TF_OUTPUT, "labels", "train"), exist_ok=True)
os.makedirs(os.path.join(TF_OUTPUT, "labels", "val"), exist_ok=True)

# ============================================================
# LABEL MAP GENERATION
# ============================================================

label_map_path = os.path.join(TF_OUTPUT, "label_map.pbtxt")

with open(label_map_path, "w") as f:
    for i, name in enumerate(CLASS_NAMES):
        f.write("item {\n")
        f.write(f"  id: {i+1}\n")  # TF uses 1-based indexing
        f.write(f"  name: '{name}'\n")
        f.write("}\n\n")

print(f"label_map.pbtxt written to {label_map_path}")

# ============================================================
# GATHER ALL IMAGE/LABEL PAIRS
# ============================================================

pairs = []

for label_file in os.listdir(labels_dir):
    if not label_file.endswith(".txt"):
        continue

    # Remove UUID prefix (everything before the first "-")
    # Extract base name from label
    """base = os.path.splitext(label_file)[0]

    # Strip UUID prefix (everything before the first "-")
    if "-" in base:
        base = base.split("-", 1)[1]"""
    

    base = os.path.splitext(label_file)[0]

    # Decode URL-encoded characters (e.g., %5C → \)
    base = urllib.parse.unquote(base)

    # Remove UUID prefix before "__"
    if "__" in base:
        base = base.split("__", 1)[1]

    # Extract only the final filename after any slashes/backslashes
    base = os.path.basename(base)




    # Find matching image
    img_path = None
    for ext in [".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"]:
        candidate = os.path.join(images_dir, base + ext)
        if os.path.exists(candidate):
            img_path = candidate
            break

    if img_path is None:
        print("WARNING: No image for label:", label_file)
        continue

    pairs.append((img_path, os.path.join(labels_dir, label_file)))

random.shuffle(pairs)

# ============================================================
# TRAIN/VAL SPLIT
# ============================================================

split_index = int(len(pairs) * TRAIN_SPLIT)
train_pairs = pairs[:split_index]
val_pairs = pairs[split_index:]

print(f"Total images: {len(pairs)}")
print(f"Train: {len(train_pairs)}")
print(f"Val: {len(val_pairs)}")

# ============================================================
# TFRecord Feature Helpers
# ============================================================

def bytes_feature(value):
    return tf.train.Feature(bytes_list=tf.train.BytesList(value=[value]))

def float_list_feature(value):
    return tf.train.Feature(float_list=tf.train.FloatList(value=value))

def int64_list_feature(value):
    return tf.train.Feature(int64_list=tf.train.Int64List(value=value))

# ============================================================
# YOLO → TFRecord Example Builder
# ============================================================

def create_tf_example(img_path, label_path):
    with tf.io.gfile.GFile(img_path, 'rb') as fid:
        encoded_image = fid.read()

    image = Image.open(io.BytesIO(encoded_image))
    width, height = image.size

    xmins, xmaxs, ymins, ymaxs = [], [], [], []
    classes_text, classes = [], []

    with open(label_path, "r") as f:
        for line in f:
            if not line.strip():
                continue

            cid, xc, yc, w, h = map(float, line.split())

            cid = int(cid)
            class_name = CLASS_NAMES[cid]

            # Convert YOLO → TF bounding boxes
            xmin = (xc - w/2)
            xmax = (xc + w/2)
            ymin = (yc - h/2)
            ymax = (yc + h/2)

            # Clip to [0,1]
            xmin = max(0, min(1, xmin))
            xmax = max(0, min(1, xmax))
            ymin = max(0, min(1, ymin))
            ymax = max(0, min(1, ymax))

            xmins.append(xmin)
            xmaxs.append(xmax)
            ymins.append(ymin)
            ymaxs.append(ymax)

            classes_text.append(class_name.encode("utf8"))
            classes.append(cid + 1)  # TF uses 1-based indexing

    tf_example = tf.train.Example(features=tf.train.Features(feature={
        'image/encoded': bytes_feature(encoded_image),
        'image/format': bytes_feature(b'jpg'),
        'image/object/bbox/xmin': float_list_feature(xmins),
        'image/object/bbox/xmax': float_list_feature(xmaxs),
        'image/object/bbox/ymin': float_list_feature(ymins),
        'image/object/bbox/ymax': float_list_feature(ymaxs),
        'image/object/class/text': bytes_feature(b" ".join(classes_text)),
        'image/object/class/label': int64_list_feature(classes),
    }))

    return tf_example

# ============================================================
# WRITE TFRECORDS
# ============================================================

def write_tfrecord(pairs, output_path, split_name):
    writer = tf.io.TFRecordWriter(output_path)

    for img_path, label_path in pairs:
        tf_example = create_tf_example(img_path, label_path)
        writer.write(tf_example.SerializeToString())

        # Copy image + label into TF_Record structure
        copy2(img_path, os.path.join(TF_OUTPUT, "images", split_name))
        copy2(label_path, os.path.join(TF_OUTPUT, "labels", split_name))

    writer.close()
    print(f"{split_name}.record written to {output_path}")

write_tfrecord(train_pairs, os.path.join(TF_OUTPUT, "train.record"), "train")
write_tfrecord(val_pairs, os.path.join(TF_OUTPUT, "val.record"), "val")

print("\nTFRecord conversion complete!")
print("Dataset ready for TensorFlow Object Detection API.")

