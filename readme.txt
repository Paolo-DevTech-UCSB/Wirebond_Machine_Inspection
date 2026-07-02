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

#################################
# Traning Review                #
#################################

Where are the folders? 
    -C:\TensorFlow_Datasets\Datasets\Dataset_3_YOLO   (last Edited 5/19/26)
        what are the statistics from the most current folder?
        Test.py --> run to get statistics on the dataset.   
           
            === CLASS SAMPLE COUNT ===
            Label files scanned: 1540

            Class 0: 277 samples
            Class 1: 108 samples
            Class 2: 72 samples
            Class 3: 177 samples
            Class 4: 3066 samples

            All class IDs are within expected range 0–4.

    from dataset.yaml --> names: ["debris", "disfigured_bond", "missing_bond", "tape_in_hole", "three_bonds"]
    Class 0 --> debris, class 1 disfigured_bond, class 2 missing bond, class 3 tape in hole, class 4 three bonds

In order to improve the model, I'd need to bolster the other samples. 
    from gemini: Target the Minority Classes, Stop Labeling Class 4 (For Now), Increase Background Variety, Use Data Augmentation

If I were to get more photos, what did I do before:
        I imported hundreds of photos to label studio,
        I hand labeled them with 1 of 5 catagories, (giving them a bounding box, and class)
        from label studio, I downloaded a (yolo w/o images zip.)
        using a custom converter, and a folder with all the original images, 
        the yolo w/o images zip was converted to a yolo with images (assigining photos to labels.)
                            
                             what can I skip now?:

        the model is working... and so I should use custom scripts to automatically increase the dataset for classes 0-3
        1. find a way to mark disired images. 
        2. use a custom script to collect those into a new folder (+images) 
            while converting thier report bounding boxes into corresponding label files (+labels)
        3. Add the new photos & labels to the corresponding folders. 
        4. run test.py on the dataset, see that classes 0-3 have grown. 


Again Gemini: The Immediate Minimum Target: ~500 per class
                The "Sweet Spot" Target: ~1,500 per clas




