import os
from wb_config import PROCESSED_DIR

CATEGORIES = ["Default", "Guard-ring", "Cal-dot", "Unprocessed"]

def get_modules():
    modules = set()
    for cat in CATEGORIES:
        folder = os.path.join(PROCESSED_DIR, cat)
        if not os.path.exists(folder):
            continue
        for f in os.listdir(folder):
            if f.lower().endswith(".png"):
                module = f.split("_")[0]
                modules.add(module)
    return sorted(list(modules))

def count_categories_for_module(module):
    counts = {cat: 0 for cat in CATEGORIES}
    counts["Other"] = 0

    for cat in CATEGORIES:
        folder = os.path.join(PROCESSED_DIR, cat)
        if not os.path.exists(folder):
            continue
        for f in os.listdir(folder):
            if f.startswith(module + "_") and f.lower().endswith(".png"):
                counts[cat] += 1

    # Count anything that slipped into other folders
    for root, dirs, files in os.walk(PROCESSED_DIR):
        for f in files:
            if f.startswith(module + "_") and f.lower().endswith(".png"):
                # If it's not in a known category folder
                folder_name = os.path.basename(root)
                if folder_name not in CATEGORIES:
                    counts["Other"] += 1

    return counts

def main():
    modules = get_modules()

    print("\n==============================")
    print(" FINAL CATEGORY BREAKDOWN")
    print("==============================\n")

    for module in modules:
        counts = count_categories_for_module(module)

        print(f"Module: {module}")
        for cat, num in counts.items():
            print(f"  {cat:15}: {num}")
        print()

if __name__ == "__main__":
    main()
