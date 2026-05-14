import os
import glob

def remap_yolo_classes(label_dir, mapping, output_dir=None):
    """
    Remaps YOLO class IDs in all .txt label files.

    Parameters:
        label_dir (str): Path to folder containing YOLO label .txt files.
        mapping (dict): Dict mapping old_class_id -> new_class_id.
                        Example: {0:0, 1:1, 2:4, 3:2, 4:3}
        output_dir (str): Optional. If None, overwrites in place.

    Returns:
        int: Number of files processed.
    """

    if output_dir is None:
        output_dir = label_dir

    os.makedirs(output_dir, exist_ok=True)

    count = 0

    for file in glob.glob(os.path.join(label_dir, "**/*.txt"), recursive=True):
        with open(file, "r") as f:
            lines = f.readlines()

        new_lines = []
        for line in lines:
            parts = line.strip().split()
            if not parts:
                continue

            old_id = int(parts[0])

            if old_id not in mapping:
                raise ValueError(f"Class ID {old_id} not found in mapping.")

            new_id = mapping[old_id]
            parts[0] = str(new_id)
            new_lines.append(" ".join(parts) + "\n")

        # Write output
        out_path = file if output_dir == label_dir else os.path.join(output_dir, os.path.basename(file))
        with open(out_path, "w") as f:
            f.writelines(new_lines)

        count += 1

    return count


mapping = {
    0: 0,   # debris
    1: 1,   # tape_in_hole
    2: 2,   # three_bonds
    3: 3,   # disfigured_bond
    4: 4    # missing_bond
}

remap_yolo_classes("path/to/labels", mapping)
