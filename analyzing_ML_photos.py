import shutil
from pathlib import Path

def organize_images():
    # Establish the absolute path to your Desktop folder
    base_dir = Path.home() / 'Desktop' / 'Wirebond_Inspector'
    
    # Use the base directory to locate the input and output folders
    master = base_dir / 'Report Module Folders'
    review = base_dir / 'Images_To_Review'
    targets = {'debris:', 'disfigured_bond:', 'missing_bond:', 'tape_in_hole:'}
    
    for mod_dir in master.iterdir():
        if not mod_dir.is_dir(): continue
            
        txt_files = list(mod_dir.glob("*.txt"))
        if not txt_files: continue
            
        problem_images = set()
        is_target = False

        with txt_files[0].open('r') as file:
            for line in file:
                line = line.strip()
                if not line: continue
                
                if line.endswith(':'):
                    is_target = line in targets
                    continue
                
                if is_target and line != '(none)':
                    problem_images.add(line.split()[0])

        if problem_images:
            out_dir = review / f"{mod_dir.name}_photos_need_review"
            out_dir.mkdir(parents=True, exist_ok=True)
            
            #these 3 lines are supposed to move the module report.txt into the images_to_review folders
            report_file = mod_dir / 'module_report.txt'
            if report_file.exists():
                shutil.copy2(report_file, out_dir / report_file.name)
            
            for img in problem_images:
                src = mod_dir / img
                if not src.exists():
                    src = mod_dir / img.replace('.png', '.jpg')
                    
                if src.exists():
                    shutil.copy2(src, out_dir / src.name)
                    
                    
#if __name__ == '__main__':
#    organize_images()