import Folder_to_Report_config
from numpy import fix
import preprocess.Default_Post_Cleanup as DPC
import preprocess.Folder_Builder as Folder_Builder
from Module_Reports_Singles import evaluate_module
import os
#run a modified version of processor master, use the new configuration file in such
print("USING wb_config FROM:", Folder_to_Report_config.__file__)

Folder_Builder.Main_Controller()

DPC.Post_Default_Cleanup()

base = Folder_to_Report_config.CONFIG["BASE_DIR"]
processed_root = os.path.join(base, Folder_to_Report_config.CONFIG["PROCESSED_DIR"])

modules = [
    d for d in os.listdir(processed_root)
    if os.path.isdir(os.path.join(processed_root, d))
]

for module in modules:
    evaluate_module(module)

