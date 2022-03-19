import dataclasses
from operator import index
from unittest import case
from xmlrpc.client import Boolean
from pykinect2 import PyKinectV2
from pykinect2 import PyKinectRuntime
import ctypes
import _ctypes
import pygame
import sys
from enum import Enum

import pykinect2
class TRACKING_STATE(Enum):
    """This is a class to describe the state of the JOINT as tracked, not tracked or infered"""
    def get_state(self, val: PyKinectV2._TrackingState) -> None:
        if val==PyKinectV2.TrackingState_NotTracked:
            return TRACKING_STATE.NotTracked
        elif val==PyKinectV2.TrackingState_Inferred:
            return TRACKING_STATE.Infered
        else:
            return TRACKING_STATE.Tracked
    NotTracked =  PyKinectV2.TrackingState_NotTracked
    Infered = PyKinectV2.TrackingState_Inferred
    Tracked = PyKinectV2.TrackingState_Tracked

@dataclasses.dataclass(unsafe_hash=True)
class JOINT:
    """data class to keep track of x, y, and state of the skeleton joint
    """
    x: float
    y: float
    state: TRACKING_STATE

index_to_joint_name = {
    0:'SpineBase',
    1:'SpineMid',
    2:'Neck',
    3:'Head',
    4:'ShoulderLeft',
    5:'ElbowLeft',
    6:'WristLeft',
    7:'HandLeft',
    8:'ShoulderRight',
    9:'ElbowRight',
    10:'WristRight',
    11:'HandRight',
    12:'HipLeft',
    13:'KneeLeft',
    14:'AnkleLeft',
    15:'FootLeft',
    16:'HipRight',
    17:'KneeRight',
    18:'AnkleRight',
    19:'FootRight',
    20:'SpineShoulder',
    21:'HandTipLeft',
    22:'ThumbLeft',
    23:'HandTipRight',
    24:'ThumbRight',
}

@dataclasses.dataclass(unsafe_hash=True)
class Skeleton:
    """mutable data class to keep track of each of the Joints also has and ID property and a color property
    
    --- USAGE --
    s= Skeleton()
    s[20] = JOINT(x=55, y=33, state=TRACKING_STATE.TRACKED) 
        this will translate to s.SpineShoulder = JOINT(x=55, y=33, state=TRACKING_STATE.TRACKED)
        which is mutating the SpineShoulder point to a new point and this is to be compatible with the output of the PyKinect output which is an index 
    """
    SpineBase: JOINT = None
    SpineMid: JOINT = None
    Neck: JOINT = None
    Head: JOINT = None
    ShoulderLeft: JOINT = None
    ElbowLeft: JOINT = None
    WristLeft: JOINT = None
    HandLeft: JOINT = None
    ShoulderRight: JOINT = None
    ElbowRight: JOINT = None
    WristRight: JOINT = None
    HandRight: JOINT = None
    HipLeft: JOINT = None
    KneeLeft: JOINT = None
    AnkleLeft: JOINT = None
    FootLeft: JOINT = None
    HipRight: JOINT= None
    KneeRight: JOINT= None
    AnkleRight: JOINT= None
    FootRight: JOINT= None
    SpineShoulder: JOINT= None
    HandTipLeft: JOINT= None
    ThumbLeft: JOINT= None
    HandTipRight: JOINT= None
    ThumbRight: JOINT= None
    ID: int= None
    tracked: bool= None
    def __setitem__(self,joint_index:int ,Joint_value: JOINT):
        setattr(self, index_to_joint_name[joint_index], Joint_value)
        
    def __getitem__(self,joint_index):
        getattr(self, index_to_joint_name[joint_index])

    
class bodySkeleton():
    """Class to get the BodySkeleton from a connected xbox Kinect V2. reads the output and then gives a readable output
    skeletons = [] which has many skeletins depending on wheather they are tracked or not with a max of 6
    skeleton is a dataclass that has data about the x, y and state of each joint point
    """
    def __init__(self, kinect=None):

        if not kinect:
            self._kinect = PyKinectRuntime.PyKinectRuntime(PyKinectV2.FrameSourceTypes_Body)
        else:
            self._kinect= kinect
        self._bodies=None
        self.skeletons = [Skeleton() for _ in range(self._kinect.max_body_count)] # this will be the main python dict that we will use to store all the info
        
    def __enter__(self):
        print('BodySkeleton Statring')
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
        if self._kinect.has_new_body_frame(): 
            self._bodies = self._kinect.get_last_body_frame()
        else:
            self._bodies = self._bodies # keep the last bodies frame as it is the last frame
            # TODO: keep track of the time it took to get this frame for sync 
        if self._bodies is not None: # if there are any bodies tracked ?? 
            for i in range(0, self._kinect.max_body_count): # for each of the max 6 ppl
                body = self._bodies.bodies[i] 
                if not body.is_tracked: # if this body is not trackable skip
                    self.skeletons[i].tracked = False
                    continue 
                
                self.skeletons[i].tracked = True
                joints = body.joints 
                # convert joint coordinates to color space 
                joint_points = self._kinect.body_joints_to_color_space(joints)
                self.skeletons[i]= self.update_body_points(joints, joint_points)
                break
        return self.skeletons
    
    def update_body_points(self, joints, joint_points):
        skeleton = Skeleton()
        for i in range(PyKinectV2.JointType_Count):
            print(i)
            print(joints[i].TrackingState)
            print(joint_points[i].x, joint_points[i].y)
            j= JOINT(x=joint_points[i].x, y=joint_points[i].y, state=TRACKING_STATE(joints[i].TrackingState))
            skeleton[i]= j
        return skeleton
class JOINTS(Enum):
    SpineBase = 1
    SpineMid = 2

if __name__ == "__main__":
    with bodySkeleton() as tracker:
        while True:
            a=tracker.get_kinect_data()            
            print(a)
            #tracker.update_body_points(None, None)




"""
sample output in my head
get_data()
the data will be a dictaionay that has a keyword for each of the 
"""