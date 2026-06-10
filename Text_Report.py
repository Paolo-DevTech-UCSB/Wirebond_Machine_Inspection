import os
import Folder_to_Report_config

def get_all_report_file_paths():
    base = Folder_to_Report_config.CONFIG["BASE_DIR"]
    report_root = os.path.join(base, Folder_to_Report_config.CONFIG["REPORT_DIR"])

    report_paths = []

    # Loop through each folder inside the report root
    for folder in os.listdir(report_root):
        folder_path = os.path.join(report_root, folder)

        # Only consider directories
        if os.path.isdir(folder_path):
            report_file = os.path.join(folder_path, "module_report.txt")

            # Only add if the file actually exists
            if os.path.isfile(report_file):
                report_paths.append(report_file)

    return report_paths

def get_report_stats(path):
    with open(path, 'r') as f:
        lines = f.readlines()
    return len(lines)



def print_report_table(report_data):
    # Two-line headers for compact width
    headers_line1 = [
        "module", "total", "nominal", "total", "three‑bond", "nominal",
        "debris", "disfig", "missing", "tape", "flags"
    ]
    headers_line2 = [
        "name", "detections", "detections", "images", "count", "3‑bond cnt",
        "count", "count", "count", "cnt", ""
    ]

    columns = [
        'module_name',
        'total_detections',
        'Nominal_Detections',
        'total_Images',
        'three_bonds_count',
        'Nominal_three_bonds_count',
        'debris_count',
        'disfigured_bond_count',
        'missing_bond_count',
        'tape_in_hole_count',
        'flags'
    ]

    col_width = 14  # slightly wider for module names

    # Header line 1
    line1 = " | ".join(f"{h:<{col_width}}" for h in headers_line1)
    print(line1)

    # Header line 2
    line2 = " | ".join(f"{h:<{col_width}}" for h in headers_line2)
    print(line2)

    print("-" * len(line1))

    # Rows
    for entry in report_data:
        row = " | ".join(f"{str(entry[col]):<{col_width}}" for col in columns)
        print(row)




def parse_module_report(path):
    def safe_int(value):
        value = value.strip()
        return int(value) if value.isdigit() else 0

    stats = {
        'total_detections': 0,
        'Nominal_Detections': 0,
        'total_Images': 0,
        'three_bonds_count': 0,
        'Nominal_three_bonds_count': 0,
        'debris_count': 0,
        'disfigured_bond_count': 0,
        'missing_bond_count': 0,
        'tape_in_hole_count': 0,
        'flags': ""
    }

    with open(path, 'r') as f:
        for line in f:
            line = line.strip()

            if line.startswith("Total images:"):
                stats['total_Images'] = safe_int(line.split(":")[1])

            if line.startswith("Module ID:"):
                stats['module_name'] = line.split(":")[1].strip()


            elif line.startswith("Total detections:"):
                stats['total_detections'] = safe_int(line.split(":")[1])

            elif line.startswith("three_bonds:"):
                val = safe_int(line.split(":")[1])
                stats['three_bonds_count'] = val
                stats['Nominal_three_bonds_count'] = val
                stats['Nominal_Detections'] = val

            elif line.startswith("debris:"):
                stats['debris_count'] = safe_int(line.split(":")[1])

            elif line.startswith("disfigured_bond:"):
                stats['disfigured_bond_count'] = safe_int(line.split(":")[1])

            elif line.startswith("missing_bond:"):
                stats['missing_bond_count'] = safe_int(line.split(":")[1])

            elif line.startswith("tape_in_hole:"):
                stats['tape_in_hole_count'] = safe_int(line.split(":")[1])

    # Auto‑flagging logic (you can customize this)
    flags = []
    if stats['debris_count'] > 0:
        flags.append("debris")
    if stats['missing_bond_count'] > 0:
        flags.append("missing")
    if stats['disfigured_bond_count'] > 0:
        flags.append("disfigured")
    if stats['tape_in_hole_count'] > 0:
        flags.append("tape")

    stats['flags'] = ", ".join(flags) if flags else "OK"

    return stats




def Main():
    print("Report file paths:", get_all_report_file_paths())
    for path in get_all_report_file_paths():
        print(f"Stats for {path}: {get_report_stats(path)}")

    report_paths = get_all_report_file_paths()

    report_data = []
    for path in report_paths:
        stats = parse_module_report(path)
        report_data.append(stats)

    print_report_table(report_data)

#Main()


    
def check_module_completeness(module):
    pathslist = get_all_report_file_paths()
    if module not in [os.path.basename(p).split("_")[0] for p in pathslist]:
        print(f"Module {module} is missing a report file.") 
        return False
    else:
        print(f"Module {module} has a report file.")
        return True