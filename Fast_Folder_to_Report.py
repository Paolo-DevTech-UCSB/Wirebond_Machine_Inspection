import Folder_to_Report_config
#from numpy import fix
import numpy as np
import preprocess.Default_Post_Cleanup as DPC
import preprocess.Dataset_Builder_Fast as Folder_Builder
from Module_Reports_Singles import evaluate_module
import os
from Folder_to_Report_config import CONFIG
import Text_Report
import analyzing_ML_photos




#syncing Pi-photos and Input Module folders folders
import copying_photo_folders
#copying_photo_folders.sync_photo_folders()

#starting process
#run a modified version of processor master, use the new configuration file in such
print("USING wb_config FROM:", Folder_to_Report_config.__file__)

Folder_Builder.Main_Controller()

DPC.Post_Default_Cleanup()

#Preprocess done by this line
print("#############################")
print("#  Preprocess DONE          #")
print("#############################")


base = Folder_to_Report_config.CONFIG["BASE_DIR"]
processed_root = os.path.join(base, Folder_to_Report_config.CONFIG["PROCESSED_DIR"])

CATEGORY_FOLDERS = set(CONFIG["MODULE_OUTPUT_FOLDERS"])

modules = [
    d for d in os.listdir(processed_root)
    if os.path.isdir(os.path.join(processed_root, d))
    and d not in CATEGORY_FOLDERS
]

#newlist = []
#print(modules)
#for module in modules:
# if not Text_report. check_nmodule_completess(module):
#    newlist.append(module)

print("this is the module processing list:", modules)

print("#############################")
print("#  Starting Model Processing#")
print("#############################")

for module in modules:
    if not Text_Report.check_module_completeness(module):
        evaluate_module(module)

Text_Report.Main()
analyzing_ML_photos.organize_images()