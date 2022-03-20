import dataclasses
from operator import index
from unittest import case
from xmlrpc.client import Boolean

import numpy as np
from pykinect2 import PyKinectV2
from pykinect2 import PyKinectRuntime
from enum import Enum
import time
class bodyIndex():
    """Class to get the BodySkeleton from a connected xbox Kinect V2. reads the output and then gives a readable output
    skeletons = [] which has many skeletins depending on wheather they are tracked or not with a max of 6
    skeleton is a dataclass that has data about the x, y and state of each joint point
    """
    def __init__(self, kinect=None):

        if not kinect:
            self._kinect = PyKinectRuntime.PyKinectRuntime(PyKinectV2.FrameSourceTypes_BodyIndex)
        else:
            self._kinect= kinect
        self._frame=None  
        self.data_shape= self._kinect.body_index_frame_desc.Height, self._kinect.body_index_frame_desc.Width
    def __enter__(self):
        print('Body Index Statring')
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

    def get_kinect_data(self):
        if self._kinect.has_new_body_index_frame(): 
            raw_data = self._kinect.get_last_body_index_frame() 
            # the data comes with 255 representing an empty pixel and index 1 to 6 representing a pixel with a person in it
            self._frame = np.reshape(raw_data, (self.data_shape[0], self.data_shape[1]))
        else:
            self._frame = self._frame # keep the last bodies frame as it is the last frame
            # TODO: keep track of the time it took to get this frame for sync 
        return self._frame


if __name__ == "__main__":
    with bodyIndex() as tracker:
        time.sleep(5)
        for i in range(2000):
            a=tracker.get_kinect_data()  
            print(a, a.shape, type(a), tracker._kinect.body_index_frame_desc.Height, tracker._kinect.body_index_frame_desc.Width)




"""
sample output in my head
get_data()
the data will be a dictaionay that has a keyword for each of the 
"""