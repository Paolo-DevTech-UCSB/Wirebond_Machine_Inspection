import os
import urllib.parse

labels_dir = r"C:\TensorFlow_Datasets\Datasets\Dataset_3_YOLO\labels\train"

for label_file in os.listdir(labels_dir):
    if not label_file.endswith(".txt"):
        continue

    old_path = os.path.join(labels_dir, label_file)

    # Remove .txt
    encoded = os.path.splitext(label_file)[0]

    # Decode URL encoding
    decoded = urllib.parse.unquote(encoded)

    # Remove UUID prefix
    if "__" in decoded:
        decoded = decoded.split("__", 1)[1]

    # Extract the real filename after last slash or %5C
    decoded = decoded.replace("\\", "/")
    decoded = decoded.split("/")[-1]

    # ❌ DO NOT remove "_processed"
    # We keep it so labels match images

    # Final YOLO label filename
    new_name = decoded + ".txt"
    new_path = os.path.join(labels_dir, new_name)

    # Skip if already correct
    if old_path == new_path:
        continue

    # Avoid overwriting
    if os.path.exists(new_path):
        print(f"SKIPPED (duplicate): {new_name}")
        continue

    print(f"{label_file}  ->  {new_name}")
    os.rename(old_path, new_path)

print("Done renaming label files.")
