from numpy import fix

import preprocess.Dataset_Builder_Fast as Dataset_Builder_Fast
import preprocess.Default_Post_Cleanup as DPC
import preprocess.post_run_category_report as post_run_category_report


import wb_config
print("USING wb_config FROM:", wb_config.__file__)

Dataset_Builder_Fast.Main_Controller()

DPC.Post_Default_Cleanup()

post_run_category_report.main()





