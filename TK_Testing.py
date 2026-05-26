from TK_Reviewer import retrieve_image_grade, Get_Module_Images, Update_Inspection_Status, read_first_module_status


basedir = r"C:\Users\hep\Desktop\Basic Inspector\Report Module Folders"


"""
size = len(Get_Module_Images("320MHF2WDSB0099"))
for i in range(size):
    print(f"Image {i} grade: {retrieve_image_grade('320MHF2WDSB0099', i)}")
#print(retrieve_image_grade("320MHF2WDSB0099", 0))

Update_Inspection_Status("320MHF2WDSB0099") 
"""

Update_Inspection_Status("320MHF2WDSB0099")
read_first_module_status("320MHF2WDSB0099")
