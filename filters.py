from abc import ABC, abstractmethod
from pkgutil import get_data
import time

import cv2
from depth import depth
import numpy as np

from scipy import signal
import collections

class filter(ABC):
 
    @abstractmethod
    def filter(self, frame: np.array):
        pass


class kernel_average_filter(filter):
       
    def __init__(self,  kernel_size: 'tuple[int, int]'=(3, 3) ) -> None:
        self.kernel_size = kernel_size
    def filter(self, depth_frame: np.ndarray):
        the_kernel= np.ones(self.kernel_size)/(self.kernel_size[0]*self.kernel_size[1])
        res = signal.convolve2d(depth_frame, the_kernel, boundary='fill', mode='same')
        #print(res.shape)
        return res


class buffer():
    """this ia a simple buffer to store a specific number of elements and get any of them consistently
    
    was made in case the implemetation needed to be more efficent """
    def __init__(self, size:int=5):

        self.size=size
        self._buffer: np.ndarray = None

    
    def add_frame(self, frame):
        if self._buffer is None:
            self._buffer = frame # if this is the 1st frame
            return
        
        self._buffer = np.dstack((self._buffer, frame))

        if self.get_size() > self.size: # if the buffer overflows
            self._buffer = np.delete(self._buffer, 0, axis=2) # remove the first Frame

    def get_data(self):
        return self._buffer
    def get_size(self):
        if self._buffer is None:
            return 0
        return self._buffer.shape[2]
    
class temporal_average_filter(filter):

    def __init__(self, temporal_length: int=5):
        """this will take m frames and give the average m frames in the past 
        be carefull not to increase m as not to take irrelavent data"""
        self.temporal_length=temporal_length
        self._buffer = buffer(size=temporal_length)

    def filter(self, frame: np.array):
        """takes a frame and then returns the average of each pixel from the previous frames while adding this frame to the buffer

        Args:
            frame (np.array): 2d frame of depth data

        Returns:
            np.ndarray: the 2d filtered depth data
        """
        if self._buffer.get_size() < self.temporal_length:
            # this is one of the 2st few frames so we will simply replicate it
            for _ in range(self.temporal_length):
                self._buffer.add_frame(frame)

        self._buffer.add_frame(frame) # add the new frame to the buffer 
        data= self._buffer.get_data() # get all the frames in the buffer
        kernel = np.ones((1, 1, self.temporal_length))  / self.temporal_length # create an avg kernel for each pixel
        
        ans= signal.convolve(data, kernel, mode='valid') # convolve to get an average of this frame and the last frames
        ans= ans[:, :, 0] # remove the depth dimestino that was added as the return is a (width, height, 1 ) and we want a (width, height)
        return ans


 
        


if __name__=='__main__':
    from tracker import tracker
    from util import save_vid
    with tracker(depth_filters=[temporal_average_filter(), kernel_average_filter(kernel_size=(9, 9))]) as tracker:
        #f= temporal_average_filter()
        img = tracker.show_depth_image()


        # frames = np.dstack( (img, img) )
        # temporal_length= 5
        # for i in range(temporal_length-2):
        #     frames = np.dstack( (frames, img) )
        

        # kernel = np.ones((1, 1, temporal_length))  / temporal_length
        # print(frames.shape, kernel.shape)
        # ans= signal.convolve(frames, kernel, mode='valid')
        # print(ans.shape, ans)
        # ans_2= frames= np.dstack((frames, ans))
        # ans_3= np.delete(frames, 0, axis=2)
        # print(ans_2.shape, ans_2)

        print('done')
        # f.filter(img)
        # after_filter= f.filter(img)
        # time.sleep(5)
        # cap = cv2.VideoCapture('temp/video.avi')
        # while(cap.isOpened()):
        #     ret, frame = cap.read()
            
        
        #     try :
        #         cv2.imshow('frame', frame)
        #     except :
        #         cap.release()
        #         cv2.destroyAllWindows() # this is becuase we want to close the window as soon as there are no more frames and sometimes the last frame is corupt
        
        #     if cv2.waitKey(1) & 0xFF == ord('q'):
        #         break        
        # cap.release()
        # cv2.destroyAllWindows()
        
        