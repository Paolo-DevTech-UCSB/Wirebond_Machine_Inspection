import Dataset_Builder_Lite


#this will be the initial system separated from the NEW system. 
#spoke detection #centering #caldot and gaurdring detection
#modifications needed: 
#      ([DONE]) no 0 output, output into another folder and inform the next pipeline.
#      ([DONE]) Caldot and Gaurdring centering needs fixing. 
#       

#included files: DataSetbuilder lite & image centering & image processing tools & wb_config


Dataset_Builder_Lite.Main_Controller()

#At this point the dataset is built, the yeilds of different classes are good enough. 
# Don't worry about the "unprocessed" and "gaurd-rings" and "cal-dots" for now, 
# just make sure the "default" class gets a second look. 

#1. making it and its called default_post_cleanup.py
#     to do:
    # edit is_sensor_color and is_FR4_color to be more accurate
    # use the merc mask for default double cleanup. 

#2. reclaim normal stepped holes from  Cal_dot, gaurd-ring, and unprocessed folders.
    # each will be unique, which helps with the pipline. 
    # for unprocessed, maybe try the color filter approach to reclaim strangly lit photos. 

#3 once default is 99% clean, start labeling and training the model.









# make an image grader ( for the stepped holes )
# this could include if theres a blue circle and green or gold around it in the right spots
# + check the mercedes mask again ( use blue cneter this time ), is it upside down? 
# 


## chore: find the average color of the "good results"
# result: if a "bad grade photo is a different average color, subtract that average difference from the rgb values in
# a temporary inputs folder, and rerun a Main_controller (just with new input folder)
# 




