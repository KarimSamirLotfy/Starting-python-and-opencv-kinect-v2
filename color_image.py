import dataclasses
from email.mime import image
from operator import index
from unittest import case
from xmlrpc.client import Boolean

import numpy as np
from pykinect2 import PyKinectV2
from pykinect2 import PyKinectRuntime
import time
  
from enum import Enum
import cv2

class colorImage:
    """class to get the color image from the Kinect V2
    """
    def __init__(self, kinect=None):
        if not kinect:
            self._kinect = PyKinectRuntime.PyKinectRuntime(PyKinectV2.FrameSourceTypes_Color)
        else:
            self._kinect= kinect
        self.last_frame=None
    def __enter__(self):
        print('ColorImage Statring')
        time.sleep(5) 
        return self
    def __exit__(self, exc_type, exc_value, exc_traceback):
        """uses context keywords to close the switch at the end
        -- USAGE--
        with bodySkeleton() as tracker:
        while True:
            skeletons=tracker.get_kinect_data()            
            print(skeletons) 

        Args:
            exc_type (_type_): _description_
            exc_value (_type_): _description_
            exc_traceback (_type_): _description_
        """
        # close the kinect when you are done to make sure it stays healthy
        self._kinect.close()
        print('bodySkeleton end')

    def get_kinect_data(self):
    # here we get the body data from kinect or simply keep the old data
        if self._kinect.has_new_color_frame(): 
            stream = self._kinect.get_last_color_frame()
            self.last_frame= np.reshape(stream, (self._kinect.color_frame_desc.Height, self._kinect.color_frame_desc.Width, 4))
        else:
            self.last_frame = self.last_frame # keep the last bodies frame as it is the last frame
            # TODO: keep track of the time it took to get this frame for sync 

        return self.last_frame

if __name__ == "__main__":
    with colorImage() as tracker:
        for i in range(2000):

            img=tracker.get_kinect_data()  
            cv2.imshow('image', img)
            if cv2.waitKey(1) == ord('q'):
                break
    cv2.destroyAllWindows()
