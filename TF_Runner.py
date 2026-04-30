import TF_Tools

savename = "Model1b"

def train_and_save(savename):
    TF_Tools.Training_Module()
    TF_Tools.Build_Model()
    TF_Tools.Model_Compiler()
    TF_Tools.train_model()
    TF_Tools.Confusion_Matrix()   # <-- moved here
    TF_Tools.Save_Model(savename)

train_and_save(savename)

def load_and_test(savename):
    # Load the model
    TF_Tools.Load_Model(savename)

    # Test all photos in the Example Photos folder
    TF_Tools.Test_Example_Photos(savename)

#load_and_test(r"Model1a")