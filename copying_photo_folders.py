import os
import shutil

source_dir = r"C:\Users\hep\Downloads\PiPhotos"
dest_dir = r"C:\Users\hep\Desktop\Wirebond_Inspector\Input Module Folders"
text_file_path = r"C:\Users\hep\Desktop\Wirebond_Inspector\photos_list.txt"

def sync_photo_folders():
    os.makedirs(dest_dir, exist_ok=True)

    #Read the historical record of folders (if the file exists)
    seen_in_history = set()
    if os.path.exists(text_file_path):
        with open(text_file_path, 'r') as file:
            # Read lines and remove empty spaces/newlines
            seen_in_history = {line.strip() for line in file if line.strip()}

    # Get current folders in piphotos
    pi_folders = [f for f in os.listdir(source_dir) if os.path.isdir(os.path.join(source_dir, f))]

    added_folders = []

    #Open the text file 
    with open(text_file_path, 'a') as history_file:
        for folder in pi_folders:
                
            # Compare PiPhotos with the list
            if folder not in seen_in_history:
                source_folder_path = os.path.join(source_dir, folder)
                dest_folder_path = os.path.join(dest_dir, folder)
                
                # Copy the folder over
                if not os.path.exists(dest_folder_path):
                    shutil.copytree(source_folder_path, dest_folder_path)
                
                # Append to the list and update active memory
                history_file.write(folder + '\n')
                seen_in_history.add(folder) 
                added_folders.append(folder)


    # The single print command
    print(f"New folders added: {', '.join(added_folders)}" if added_folders else "No new folders were added.")

sync_photo_folders()