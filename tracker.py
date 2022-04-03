import dataclasses
import math
from operator import index
import time
from tkinter import S
from unittest import case
from xmlrpc.client import Boolean

from numpy import dtype
from body_index import bodyIndex
from body_skeleton import JOINT, TRACKING_STATE, Skeleton
from depth import depth
from filters import kernel_average_filter, temporal_average_filter
from pykinect2 import PyKinectV2
from pykinect2 import PyKinectRuntime
import ctypes
import _ctypes

from enum import Enum
import cv2
from body_skeleton import bodySkeleton
from color_image import colorImage
import numpy as np

import pykinect2
class tracker_types(Enum):
    BODY_SKELTETON= bodySkeleton
    COLOR_IMAGE= colorImage
class tracker:
    """class that gives all vues using funciton calls also has a debugger screen for all the views in opencv2
    """
    COLORS= [
        [252, 186, 3],
        [48, 250, 2 ],
        [2, 247, 223],
        [2, 158, 247],
        [5, 5, 242],
        [205, 7, 240]
    ]
    def __init__(self, depth_filters: 'list[filter]'=[]) -> None:
        self.depth_filters = depth_filters

        # TODO: for each tracker make the Runtime with the output
        self._kinect = PyKinectRuntime.PyKinectRuntime(PyKinectV2.FrameSourceTypes_Body | PyKinectV2.FrameSourceTypes_Color | PyKinectV2.FrameSourceTypes_BodyIndex | PyKinectV2.FrameSourceTypes_Depth)
        self._body_skeleton= bodySkeleton(self._kinect)
        self._color_image= colorImage(self._kinect)
        self._body_index = bodyIndex(self._kinect)
        self._depth=depth(self._kinect)
    def __enter__(self):
        time.sleep(3) # give the kinect 3 seconds to boot up 
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
       
        data= list(filter(lambda x: x.tracked, data))
        return data # send only data of the tracked bodies not the rest
    def get_index_data(self):
        data= self._body_index.get_kinect_data()
        return data

    def show_index_body(self, return_img=False):
        """method that displays the camera at max size"""
        def index_to_color_mapper(element):
            
            if element > len(self.COLORS):
                return np.array([0, 0, 0], dtype=np.uint8)
            return np.array(self.COLORS[element], dtype=np.uint8)
        while True:
            img=self.get_index_data() 
            shape=img.shape + (3,)
            img= img.flatten()
            img = np.array(list(map(index_to_color_mapper, img)))
            img=np.reshape(img, shape)
            # img= img.astype(np.uint8)

            if return_img:
                return img
            cv2.imshow('image', img)
            if cv2.waitKey(1) == ord('q'):
                break
        cv2.destroyAllWindows()

    def get_depth_data(self):
        data= self._depth.get_kinect_data()
        #print(data[55:70, 100:120])
        for depth_filter in self.depth_filters:
            data = depth_filter.filter(data)
        #print(data[55:70, 100:120])
        
        return data

    def get_body_data_with_depth(self):
        data_depth= self.get_depth_data() # is in form (424, 512)
        data_body= self.get_body_data() # relative to cam data which is (1080, 1920)
        cam_width, cam_height = 1920, 1080
        depth_width, depth_height = 512, 424  

        # here we add the depth data for each joint if you want it to be used
        for body in data_body:
            for i in range(PyKinectV2.JointType_Count):
                if body[i].state != TRACKING_STATE.Tracked: # if this is not tracked skip adding the depth to it
                    continue
                x, y = body[i].x, body[i].y # real x and y in cam image
                #print(f'points:{x, y}')
                xs,ys = math.floor((x * depth_width)/cam_width), math.floor((y * depth_height)/cam_height)

                depth : np.ndarray = data_depth[min(xs, 423),  min(ys, 511)]
                body[i].z= depth.astype(np.int32)
                


           
        return data_body


    
    def show_depth_image(self, return_img=False):
        while True:
            img= self.get_depth_data()
            img_color_space= np.rint(np.interp(img, (0, 6000), (0, 255))).astype(np.uint8)
            if return_img:
                return img_color_space
            cv2.imshow('image', img_color_space)
            if cv2.waitKey(1) == ord('q'):
                break
        cv2.destroyAllWindows()

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


    def show_hand_proximity(self, return_img=False, with_depth_img=False):
        """shows on your hand a circle that growns bigger the closer your hand is relative to the depth sensor"""
        LEFT_HAND_INDEX= 12
        while True:
            img= self.show_camera_skeleton(return_img=True)
            body_data=self.get_body_data_with_depth()
            
           
            
            time.sleep(0.2)
            
            # Center coordinates
            #print(body_data)
            for body in body_data:
                if not body.tracked:
                    continue
                left_hand_x, left_hand_y, left_hand_depth, state = body[LEFT_HAND_INDEX].x, body[LEFT_HAND_INDEX].y, body[LEFT_HAND_INDEX].z, body[LEFT_HAND_INDEX].state
                if state == TRACKING_STATE.Tracked:
            
                    center_coordinates = (int(left_hand_x), int(left_hand_y))
                    
                    # Radius of circle
                    # radius = np.interp(left_hand_depth, (100, 5000), (300, 10))[0]
                    # radius = radius.astype(np.int8)
                    radius = 30
                    #print(f'{radius}, {type(radius)}')
                    # Blue color in BGR
                    color = (255, 0, 0)
                    
                    # Line thickness of 2 px
                    thickness = 2
                    cv2.circle(img, center_coordinates, radius, color, thickness)
                    font = cv2.FONT_HERSHEY_SIMPLEX


                    
                    cv2.putText(img, f'depth:{left_hand_depth}', (10,450), font, 3, (0, 255, 0), 2, cv2.LINE_AA)
                    cv2.putText(img, f'pos:{center_coordinates}', (15,450), font, 3, (0, 255, 0), 2, cv2.LINE_AA)
                    # cv2.putText(img, f'pos in color image:{center_coordinates}', (15,450), font, 3, (0, 255, 0), 2, cv2.LINE_AA)
                    # cv2.putText(img, f'depth after depth:{center_coordinates}', (15,450), font, 3, (0, 255, 0), 2, cv2.LINE_AA)


               
            if return_img:
                return img
            
            

            
            cv2.imshow('image', img)
            if cv2.waitKey(1) == ord('q'):
                break
        cv2.destroyAllWindows()     
            
    def show_img_skeleton_and_depth_img_of_joint(self, JOINT_INDEX:int= 12, return_img=False) -> 'tuple[np.ndarray, np.ndarray]':
        import demo.mapper as mp
        while True:
            
            img= self.show_camera_skeleton(return_img=True)
            body_data=self.get_body_data_with_depth()      

            ### depth data
            data_depth= self.get_depth_data() # is in form (424, 512)
            cam_width, cam_height = 1920, 1080
            depth_width, depth_height = 512, 424        
            depth_img= self.show_depth_image(return_img=True)
            for body in body_data:
                if not body.tracked:
                    continue
                left_hand_x, left_hand_y, left_hand_depth, state = body[JOINT_INDEX].x, body[JOINT_INDEX].y, body[JOINT_INDEX].z, body[JOINT_INDEX].state
                if state == TRACKING_STATE.Tracked:
                    center_coordinates = (int(left_hand_x), int(left_hand_y))
                    radius = 30
                    color = (255, 0, 0)
                    thickness = 2
                    cv2.circle(img, center_coordinates, radius, color, thickness)
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    cv2.putText(img, f'depth:{left_hand_depth}', (10,450), font, 3, (0, 255, 0), 2, cv2.LINE_AA)


                ### add the depth img
                x, y = body[JOINT_INDEX].x, body[JOINT_INDEX].y # real x and y in cam image
               
                # xs,ys = joints_depths = self._kinect.body_joint_to_depth_space() # maps the camera coordinates to the depth image we keda 
                # xs, ys= mp.depth_2_color_space(self._kinect, PyKinectV2._DepthSpacePoint, self._kinect._depth_frame_data)

                # draw circle in depth img 
                depth_img = cv2.cvtColor(depth_img, cv2.COLOR_GRAY2RGB)
                #cv2.circle(depth_img, center=(xs, ys), radius=20, color=(255, 0, 0), thickness=2)

                
               
            if return_img:
                return (img, depth_img)
            
            

            
            cv2.imshow('image', img)
            cv2.imshow('depth image', depth_img)
            if cv2.waitKey(1) == ord('q'):
                break
        cv2.destroyAllWindows()   



if __name__ == "__main__":
    with tracker(depth_filters=[temporal_average_filter(temporal_length=30)]) as trkr:
        time.sleep(5)
        timeout = 4   # [seconds]
        timeout_start = time.time()
        while time.time() < timeout_start + timeout:
            a= trkr.show_img_skeleton_and_depth_img_of_joint(JOINT_INDEX=0) # 3 head, 0 spine base
            
            
      
        



