import numpy as np
import cv2
import pickle
import time 
import datetime

from pykinect2 import PyKinectV2
from pykinect2.PyKinectV2 import *
from pykinect2 import PyKinectRuntime

def save_frames(FILE_NAME):
    #records and saves colour and depth frames from the Kinect
    
    # print("Saving colour and depth frames")
    
    # # define file names
    # depthfilename = "DEPTH." + FILE_NAME +".pickle"
    # colourfilename = "COLOUR." + FILE_NAME +".pickle"
    # depthfile = open(depthfilename, 'wb')
    # colourfile = open(colourfilename, 'wb')
    
    #initialise kinect recording, and some time variables for tracking the framerate of the recordings
    kinect = PyKinectRuntime.PyKinectRuntime(PyKinectV2.FrameSourceTypes_Color | PyKinectV2.FrameSourceTypes_Depth | PyKinectV2.FrameSourceTypes_Body | PyKinectV2.FrameSourceTypes_BodyIndex )
    starttime = time.time()
    oldtime = 0
    i = 0
    fpsmax = 0
    fpsmin = 100
    
    display_type = "COLOUR"
    #display_type = "DEPTH"
    
    # Actual recording loop, exit by pressing escape to close the pop-up window
    while True:

        if kinect.has_new_color_frame():
            frame = kinect.get_last_color_frame()
            #print(frame)
            frame = None

    # --- Cool! We have a body frame, so can get skeletons
        if kinect.has_new_body_frame(): 
            bodies = kinect.get_last_body_frame()
            print(bodies)
            bodies=None
        
        if kinect. has_new_body_index_frame(): 
            bodies = kinect.get_last_body_index_frame()
            #print((bodies.shape))
            bodies=None


        #end recording if the escape key (key 27) is pressed
       
    
if __name__ == "__main__":

    #Save colour and depth frames
    save_frames("file_name")