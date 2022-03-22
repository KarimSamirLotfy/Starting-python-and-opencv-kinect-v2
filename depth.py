import dataclasses
from operator import index
from unittest import case
from xmlrpc.client import Boolean

import numpy as np
from pykinect2 import PyKinectV2
from pykinect2 import PyKinectRuntime
from enum import Enum
import time
class depth():
    """Class to get the Depth from a connected xbox Kinect V2. reads the output and then gives a readable output
   
    """
    def __init__(self, kinect=None):

        if not kinect:
            self._kinect = PyKinectRuntime.PyKinectRuntime(PyKinectV2.FrameSourceTypes_BodyIndex | PyKinectV2.FrameSourceTypes_Depth | PyKinectV2.FrameSourceTypes_Infrared)
        else:
            self._kinect= kinect
        self._frame=None  
        self.data_shape= self._kinect.depth_frame_desc.Height, self._kinect.depth_frame_desc.Width
    def __enter__(self):
        print('Depth Camera Statring')
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
        print('Body index end')

    def get_kinect_data(self) -> 'np.ndarray | None':
        if self._kinect.has_new_depth_frame(): 
            raw_data = self._kinect.get_last_depth_frame() 
            
            # the data comes with 255 representing an empty pixel and index 1 to 6 representing a pixel with a person in it
            self._frame = np.reshape(raw_data, (self.data_shape[0], self.data_shape[1]))
            # self._frame= raw_data
        else:
            self._frame = self._frame # keep the last bodies frame as it is the last frame
            # TODO: keep track of the time it took to get this frame for sync 
        return self._frame


if __name__ == "__main__":
    with depth() as tracker:
        time.sleep(10)
        for i in range(2000):
            a=tracker.get_kinect_data() # data in milimeters from 0 to 8000
            print(a, a.shape ,type(a), tracker._kinect.depth_frame_desc.Height, tracker._kinect.depth_frame_desc.Width, np.max(a), np.min(a), np.average(a))

