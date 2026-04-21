from PIL import Image
import os
import numpy as np
import matplotlib.pyplot as plt
import Inital_Image_Processor_DSKTP as IIP


def Main(Current_Module, Image_Name):
    Current_Module = "MHF1WCSB0005"  # Set the current module name

    working_dir = os.getcwd()  # Get current working directory
    img = Image.open(os.path.join(working_dir, "Training_Images", Current_Module, Image_Name))  # Open the image file

    PCBX, PCBY, more_above = IIP.Main(Current_Module, Image_Name)

    cropped_img = img.crop((400 + PCBX, 375 + PCBY, 1400 + PCBX, 1200 + PCBY))  # Crop the image to a 1000x825 area centered around the PCB hole
    if more_above:
        flipped_img = cropped_img.transpose(Image.FLIP_TOP_BOTTOM)  # Flip the cropped image vertically
    else:
        flipped_img = cropped_img  # Keep the cropped image as is if no flipping is needed
    
    flipped_img.show()  # Display the flipped image

Image_List = ["10_22_23.png", "1_13_14.png", "2_3_15.png", "11_12_24.png"]

for image_name in Image_List:
    Main("MHF1WCSB0005", image_name)

