import os

# CHANGE THIS to your actual Windows username
USER = "Admin"

# Base folder on your Desktop where all PCB data lives
DATA_ROOT = fr"C:\Users\{USER}\Desktop\Wirebond Inspector"

# Subfolders inside PCB_Data
RAW_DIR = os.path.join(DATA_ROOT, "Raw Photos")
PROCESSED_DIR = os.path.join(DATA_ROOT, "Processed Photos")
LABEL_DIR = os.path.join(DATA_ROOT, "Labels")

# Make sure the folders exist (optional but helpful)
os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)
os.makedirs(LABEL_DIR, exist_ok=True)

