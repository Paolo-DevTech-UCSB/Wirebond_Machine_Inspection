This Repo Hosts the ful controlls of managing and training the Wirebond Machine Inspection, running on tensor flow.




Lessons that are important for getting this to work:

 
 
there are TWO viable approaches to building a labeled dataset:

1. USE Synced dataset --> YOLO --> use UUID stripping TF_converter Code. 

2. Use manual dataset --> YOLO W/ IMAGES -> OLD TF_converter without UUID Stripping.  




Label IMAGE LINKS BREAK when trying to automagically add photos to the tasklist
 avoid this by NOT USING YOLO w/ IMAGES




at the end of monday night i was trying to do tesnfor obj dectection api but that was too hard, 
its better that I switch to YOLOv8 becuase its simpler and will go closer to how the classiffication models went

Currently, There's a ferw steps to getting to a module report,

1st. Module Folder is Manualy Imported from Wirebond Manchines

2nd. The Processor_Master.py and preprecoess scripts are used to crop and save those photos
into the default, caldot, unprocessed and gaurdring folders. 

3rd. Module_reports_singles.py uses the photos in default to build a module level report


Lets Streamline this into One Folder, One Repo. 

----------------------------------------------

Folder to Report (time):

20 Minutes, 16 to Preprocess, 4 to Model Grading. 

-I should remake processor master, need a "Fast" processor master. 

that happened 

But now its time to finish:  Fast_folder_to_Report.py

- its still slow as hell, but also not reliable.  lets fix that
-I was trying to get the post process in better shape. (thursday night)
i think a better approach would be to improve the FIRST center detector and / or skip it for a default crop. 
 
 running out of brain power.....     
