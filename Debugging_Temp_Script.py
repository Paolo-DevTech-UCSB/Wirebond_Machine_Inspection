import os

YOLO_IMAGES = r"C:\Users\hep\Desktop\Wirebond_Inspector\YOLO_Datasets\Dataset 1\project-1-at-2026-04-21-16-30-40aa3357\images"
YOLO_LABELS = r"C:\Users\hep\Desktop\Wirebond_Inspector\YOLO_Datasets\Dataset 1\project-1-at-2026-04-21-16-30-40aa3357\labels"

img_files = [f for f in os.listdir(YOLO_IMAGES)]
label_files = [f for f in os.listdir(YOLO_LABELS)]

print("Images:", len(img_files))
print("Labels:", len(label_files))
