import os

# Find project root automatically
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_ROOT = r"C:\Users\hep\Desktop\Wirebond_Inspector"

RAW_DIR = os.path.join(DATA_ROOT, "Raw Photos")
PROCESSED_DIR = os.path.join(DATA_ROOT, "Processed Photos")
LABEL_DIR = os.path.join(DATA_ROOT, "Labels")
UNPROCESSED_DIR = os.path.join(DATA_ROOT, "Unprocessed")

os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)
os.makedirs(LABEL_DIR, exist_ok=True)
os.makedirs(UNPROCESSED_DIR, exist_ok=True)
