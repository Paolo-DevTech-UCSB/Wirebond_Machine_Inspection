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


