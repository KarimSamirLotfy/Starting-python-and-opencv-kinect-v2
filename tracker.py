import dataclasses
import math
from operator import index
import time
from tkinter import S
from unittest import case
from xmlrpc.client import Boolean
from body_skeleton import JOINT, TRACKING_STATE, Skeleton
from pykinect2 import PyKinectV2
from pykinect2 import PyKinectRuntime
import ctypes
import _ctypes

from enum import Enum
import cv2
from body_skeleton import bodySkeleton
from color_image import colorImage
import numpy as np
class tracker_types(Enum):
    BODY_SKELTETON= bodySkeleton
    COLOR_IMAGE= colorImage
class tracker:
    """class that gives all vues using funciton calls also has a debugger screen for all the views in opencv2
    """
    def __init__(self, *args: tracker_types) -> None:
        

        # TODO: for each tracker make the Runtime with the output
        self._kinect = PyKinectRuntime.PyKinectRuntime(PyKinectV2.FrameSourceTypes_Body | PyKinectV2.FrameSourceTypes_Color)
        self._body_skeleton= bodySkeleton(self._kinect)
        self._color_image= colorImage(self._kinect)

    def __enter__(self):
        print('tracker started')
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
    def get_body_data(self):
        data=self._body_skeleton.get_kinect_data()
        #print(data, sep='\n')
        data= list(filter(lambda x: x.tracked, data))
        return data # send only data of the tracked bodies not the rest
    
    def get_camera_data(self):
        data= self._color_image.get_kinect_data()
        return data
    def show_camera(self, return_img=False):
        """method that displays the camera at max size"""
        while True:
            img=self.get_camera_data()  
            if return_img:
                return img
            cv2.imshow('image', img)
            if cv2.waitKey(1) == ord('q'):
                break
        cv2.destroyAllWindows()

    def show_skeleton(self, return_img=False):
        while True:
            img= np.zeros((self._kinect.color_frame_desc.Height, self._kinect.color_frame_desc.Width, 4))
            body_data = self.get_body_data()  
            img= self.draw_skeletons(img, body_data)
            if return_img:
                return img
            cv2.imshow('image', img)
            if cv2.waitKey(1) == ord('q'):
                break
        cv2.destroyAllWindows()


    def show_camera_skeleton(self, return_img=False):
        while True:
            img1 = self.show_skeleton(return_img=True)
            img2 = self.show_camera(return_img=True)
            print(img1, img2, sep='-----------\n' ,end='--------- >>> ---------<<< \n')
            img = cv2.addWeighted(img1, 0.5, img2, 0.5, 0, dtype = cv2.CV_8U) # choosing the datype is because of a short lived bug in cv2 version 4.04
            if return_img:
                return img
            cv2.imshow('image', img)
            if cv2.waitKey(1) == ord('q'):
                break
        cv2.destroyAllWindows()            

    def draw_skeletons(self, img: np.array, body_data: 'List[Skeleton]'):
        for body in body_data:
            self.draw_body_bones(img, body)
        return img
            
    def draw_body_bones(self, img, body: Skeleton):
        color=(255, 255, 0)
        self.draw_body_bone(img, body, PyKinectV2.JointType_Head, PyKinectV2.JointType_Neck);
        # Torso
        self.draw_body_bone(img, body, PyKinectV2.JointType_Head, PyKinectV2.JointType_Neck);
        self.draw_body_bone(img, body, PyKinectV2.JointType_Neck, PyKinectV2.JointType_SpineShoulder);
        self.draw_body_bone(img, body, PyKinectV2.JointType_SpineShoulder, PyKinectV2.JointType_SpineMid);
        self.draw_body_bone(img, body, PyKinectV2.JointType_SpineMid, PyKinectV2.JointType_SpineBase);
        self.draw_body_bone(img, body, PyKinectV2.JointType_SpineShoulder, PyKinectV2.JointType_ShoulderRight);
        self.draw_body_bone(img, body, PyKinectV2.JointType_SpineShoulder, PyKinectV2.JointType_ShoulderLeft);
        self.draw_body_bone(img, body, PyKinectV2.JointType_SpineBase, PyKinectV2.JointType_HipRight);
        self.draw_body_bone(img, body, PyKinectV2.JointType_SpineBase, PyKinectV2.JointType_HipLeft);
    
        # Right Arm    
        self.draw_body_bone(img, body, PyKinectV2.JointType_ShoulderRight, PyKinectV2.JointType_ElbowRight);
        self.draw_body_bone(img, body, PyKinectV2.JointType_ElbowRight, PyKinectV2.JointType_WristRight);
        self.draw_body_bone(img, body, PyKinectV2.JointType_WristRight, PyKinectV2.JointType_HandRight);
        self.draw_body_bone(img, body, PyKinectV2.JointType_HandRight, PyKinectV2.JointType_HandTipRight);
        self.draw_body_bone(img, body, PyKinectV2.JointType_WristRight, PyKinectV2.JointType_ThumbRight);

        # Left Arm
        self.draw_body_bone(img, body, PyKinectV2.JointType_ShoulderLeft, PyKinectV2.JointType_ElbowLeft);
        self.draw_body_bone(img, body, PyKinectV2.JointType_ElbowLeft, PyKinectV2.JointType_WristLeft);
        self.draw_body_bone(img, body, PyKinectV2.JointType_WristLeft, PyKinectV2.JointType_HandLeft);
        self.draw_body_bone(img, body, PyKinectV2.JointType_HandLeft, PyKinectV2.JointType_HandTipLeft);
        self.draw_body_bone(img, body, PyKinectV2.JointType_WristLeft, PyKinectV2.JointType_ThumbLeft);

        # Right Leg
        self.draw_body_bone(img, body, PyKinectV2.JointType_HipRight, PyKinectV2.JointType_KneeRight);
        self.draw_body_bone(img, body, PyKinectV2.JointType_KneeRight, PyKinectV2.JointType_AnkleRight);
        self.draw_body_bone(img, body, PyKinectV2.JointType_AnkleRight, PyKinectV2.JointType_FootRight);

        # Left Leg
        self.draw_body_bone(img, body, PyKinectV2.JointType_HipLeft, PyKinectV2.JointType_KneeLeft);
        self.draw_body_bone(img, body, PyKinectV2.JointType_KneeLeft, PyKinectV2.JointType_AnkleLeft);
        self.draw_body_bone(img, body, PyKinectV2.JointType_AnkleLeft, PyKinectV2.JointType_FootLeft);

    def draw_body_bone(self, img, body:Skeleton, joint_1, joint_2, color=(255, 0, 255) ):
        joint1: JOINT= body[joint_1]
        joint2: JOINT= body[joint_1]

        # check that the number is within a resonable range
        if math.isinf(joint1.x) or math.isinf(joint1.y) or math.isinf(joint2.x) or math.isinf(joint2.y):
            return
        if joint1.state != TRACKING_STATE.Tracked or joint2.state != TRACKING_STATE.Tracked:
            return
        try:
            starting_point = int( body[joint_1].x), int(body[joint_1].y)
            end_point = int(body[joint_2].x), int(body[joint_2].y)
            cv2.line(img, starting_point, end_point, color=color)
        except OverflowError: # sometimes the numbers are infinty
            pass # do not draw anything
        return None

if __name__ == "__main__":
    with tracker(tracker_types.BODY_SKELTETON, tracker_types.COLOR_IMAGE) as trkr:
        time.sleep(3)
        trkr.show_camera_skeleton()



