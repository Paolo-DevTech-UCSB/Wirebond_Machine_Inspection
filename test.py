import os

root = r"C:\TensorFlow_Datasets\Datasets\Dataset_3_YOLO\labels\train"

missing = []
empty = []

for f in os.listdir(root):
    if f.endswith(".txt"):
        path = os.path.join(root, f)
        if os.path.getsize(path) == 0:
            empty.append(f)

print("Empty label files:", empty)
