"""
===========================================================
   HELPER FUNCTIONS FOR WIREBOND INSPECTOR CLEANUP SYSTEM
===========================================================

Place this file in your project and import functions like:

    from helpers_file_management import (
        load_checked_list,
        save_checked_entry,
        extract_raw_prefix,
        find_raw_image,
        ensure_folder,
        log_move
    )

These helpers are designed to:
- Track which processed images have already been handled
- Extract RAW filenames safely from processed filenames
- Locate RAW images even with inconsistent naming
- Keep module folders organized
- Log file movements for debugging
"""

import os
import re


# -----------------------------------------------------------
#  CHECKED LIST MANAGEMENT
# -----------------------------------------------------------

def load_checked_list(module_dir):
    """
    Loads the checked.txt file for a module.
    Returns a Python set of filenames already processed.

    Usage:
        checked = load_checked_list(module_dir)
        if filename in checked:
            continue  # skip already processed
    """
    checked_path = os.path.join(module_dir, "checked.txt")

    if not os.path.exists(checked_path):
        return set()

    with open(checked_path, "r") as f:
        return set(line.strip() for line in f)


def save_checked_entry(module_dir, filename):
    """
    Appends a filename to the module's checked.txt list.

    Usage:
        save_checked_entry(module_dir, filename)
    """
    checked_path = os.path.join(module_dir, "checked.txt")

    with open(checked_path, "a") as f:
        f.write(filename + "\n")


# -----------------------------------------------------------
#  RAW FILENAME EXTRACTION
# -----------------------------------------------------------

def extract_raw_prefix(processed_filename):
    """
    Extracts the RAW coordinate tail from a processed filename.

    Example:
        320MHF2TDSB0091_118_119_138_processed.png
        → "118_119_138"

    This function:
    - Removes "_processed"
    - Splits by underscores
    - Walks backward collecting numeric parts
    - Stops when non-numeric part is reached
    - Returns the last 1–3 numeric groups joined by "_"

    Usage:
        raw_prefix = extract_raw_prefix(filename)
        if raw_prefix is None:
            skip image
    """

    base = os.path.splitext(processed_filename)[0]
    base = base.replace("_processed", "")

    parts = base.split("_")
    raw_parts = []

    # Walk backwards collecting numeric parts
    for p in reversed(parts):
        if p.isdigit():
            raw_parts.append(p)
        else:
            break

    if not raw_parts:
        return None

    raw_parts.reverse()
    return "_".join(raw_parts)


# -----------------------------------------------------------
#  RAW IMAGE LOCATOR
# -----------------------------------------------------------

def find_raw_image(module, raw_prefix, RAW_DIR):
    """
    Searches the module's RAW folder for any file starting with raw_prefix.

    Example:
        raw_prefix = "118_119_138"
        → matches:
            118_119_138.png
            118_119_138_0.png
            118_119_138_original.png

    Usage:
        raw_path = find_raw_image(module, raw_prefix, RAW_DIR)
        if raw_path is None:
            skip image
    """

    module_dir = os.path.join(RAW_DIR, module)

    if not os.path.exists(module_dir):
        return None

    for f in os.listdir(module_dir):
        if f.startswith(raw_prefix):
            return os.path.join(module_dir, f)

    return None


# -----------------------------------------------------------
#  FOLDER UTILITIES
# -----------------------------------------------------------

def ensure_folder(path):
    """
    Ensures a folder exists. Creates it if missing.

    Usage:
        ensure_folder(os.path.join(PROCESSED_DIR, "Unprocessed"))
    """
    os.makedirs(path, exist_ok=True)


# -----------------------------------------------------------
#  LOGGING UTILITIES
# -----------------------------------------------------------

def log_move(src, dst):
    """
    Prints a clean log message for file moves.

    Usage:
        log_move(old_path, new_path)
    """
    print(f"Moved → {os.path.basename(src)}  →  {os.path.basename(dst)}")



# -----------------------------------------------------------
#  MODULE SUMMARY TRACKING
# -----------------------------------------------------------

def init_module_summary():
    """
    Creates a fresh summary dictionary for a module.
    Call this at the start of processing each module.
    """
    return {
        "checked": 0,
        "ok": 0,
        "bad": 0,
        "raw_missing": 0,
        "center_fail": 0,
        "moved_unprocessed": 0,
        "reclassified": 0
    }


def print_module_summary(module, summary):
    """
    Prints a clean summary for a module after processing.
    """
    print("\n====================================")
    print(f" SUMMARY FOR MODULE: {module}")
    print("====================================")
    print(f"Checked:            {summary['checked']}")
    print(f"Passed OK:          {summary['ok']}")
    print(f"Failed (BAD):       {summary['bad']}")
    print(f"RAW missing:        {summary['raw_missing']}")
    print(f"Center failures:    {summary['center_fail']}")
    print(f"Moved → Unprocessed:{summary['moved_unprocessed']}")
    print(f"Reclassified:       {summary['reclassified']}")
    print("====================================\n")
