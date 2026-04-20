from numpy import fix

import Dataset_Builder_Lite
import Default_Post_Cleanup as DPC
import post_run_category_report



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

#Default folder gets up to 95% accuracy with current setup (4/20/26)


DPC.Post_Default_Cleanup()

    #3 once default is 99% clean, start labeling and training the model.

#Default folder reached 98& accuracy with current setup (4/20/26)

#last few bugs before tesnorflow:
    #fix 0_0_0 names
    #Need a location summary for the post cleanup, so we can see which modules are doing well and which are not.

post_run_category_report.main()

#bugs for after tesnor flow:
    #1. default_post_cleanup.py  ----> use the merc mask for default double cleanup. 
    #2. reclaim normal stepped holes from  Cal_dot, gaurd-ring, and unprocessed folders.
        # each will be unique, which helps with the pipline. 
        # for unprocessed, maybe try the color filter approach to reclaim strangly lit photos. 
            ## chore: find the average color of the "good results"














# result: if a "bad grade photo is a different average color, subtract that average difference from the rgb values in
# a temporary inputs folder, and rerun a Main_controller (just with new input folder)
# 




