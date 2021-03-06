import dataclasses
from datetime import date, datetime, timedelta
import math
from operator import index
import random
import sys
import time
from tkinter import S
from unittest import case
from xmlrpc.client import Boolean

from numpy import dtype
from body_index import bodyIndex
from body_skeleton import HAND_STATE, JOINT, TRACKING_STATE, Skeleton
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
from tracker import tracker
from filters import buffer
# event handeling libary 
import smokesignal
# for writing on disk
import os
import pickle


class GAME_EVENTS(Enum):
    USER_REQUEST_CONTROL = 'USER_REQUEST_CONTROL'
    USER_GIVE_CONTROL = 'USER_GIVE_CONTROL'
    ADD_BRUSH = 'ADD_BRUSH'
    REMOVE_BRUSH = 'REMOVE_BRUSH'
class BRUSH_STATE(Enum):
    DRAWING = 0
    OFF = 1
    ERASE = 2

class GESTURES(Enum):
    RAISE_RIGHT_HAND = 1
    RAISE_LEFT_HAND = 2
    CLOSEING_LEFT_HAND = 3
    CLOSEING_RIGHT_HAND = 4
    OPENING_LEFT_HAND = 5
    OPENING_RIGHT_HAND = 5


class player:
    """a class that symbbolises 1 of the players in the game
    """
# RED = (0, 0, 255)
# GREEN = (0, 255, 0)
# BLUE = (255, 0, 0)
# CYAN = (255, 255, 0)
# MAGENTA = (255, 0, 255)
# YELLOW = (0, 255, 255)
# WHITE = (255, 255, 255)
    colors: 'list[tuple[int]]' = [
        (0, 0, 255),
        (0, 255, 0),
        (255, 255, 0),
        (255, 0, 0),
        (255, 0, 255),
        (255, 255, 255)
    ]
    # dict that maps each object number to a player ID in case it is used
    known_skeletons = {

    }
    def __init__(self, body:Skeleton) -> None:
        self.body=body
        random.shuffle(player.colors)
        self.color =  player.colors.pop()
        self.id = id(self) # get the ID from the object refrence

    def doing_gesture(self, gesture:GESTURES):
        if gesture == GESTURES.RAISE_RIGHT_HAND: # detect if the user raised his right hand 
            # if wrist is higher than shoulder then simply detect right hand
            hand_y_pos, hand_state = self.body.WristRight.y, self.body.WristRight.state
            shoulder_y_pos= self.body.ShoulderRight.y
            # TODO: this is too simple we need somehting to caluclate angle between wrist and elbow to create wheather the hand is raised or not
            if self.body.tracked and hand_state and hand_y_pos < shoulder_y_pos + 20: # if the body and the hand are tracked alos the handis higher than shoulder
                return True

        if gesture == GESTURES.RAISE_LEFT_HAND: # detect if the user raised his right hand 
            # if wrist is higher than shoulder then simply detect right hand
            hand_y_pos, hand_state = self.body.WristLeft.y, self.body.WristLeft.state
            shoulder_y_pos= self.body.ShoulderLeft.y
            # TODO: this is too simple we need somehting to caluclate angle between wrist and elbow to create wheather the hand is raised or not
            if self.body.tracked and hand_state and hand_y_pos < shoulder_y_pos + 20: # if the body and the hand are tracked alos the handis higher than shoulder
                return True
            
        if gesture == GESTURES.CLOSEING_RIGHT_HAND: # detect if the user is closing their hand
            if self.body.get_right_hand_state() == HAND_STATE.Closed:
                return True
        if gesture == GESTURES.OPENING_RIGHT_HAND: # detect if the user is closing their hand
            if self.body.get_right_hand_state() == HAND_STATE.Open:
                return True

        return False  

            

class clapGame:
    """this is a game that uses the kinect as the basis to choose a main player that will be able to clap with only 1 player being able to clap at a time
    """
    CHECKPOINT_MS=2 # every 20 milliseconds the system will take a snapshot

    def __init__(self) -> None:
        self.players: 'list[player]'= []
        self.main_user: 'player' = None
        self.requesting_players = [] # a quee of requesting players so that if 2 ppl request then they get it in order
        self.img_buffer: 'list[np.array]' = []
        self.players_buffer = []
        self.video_writer = None
        time_now = datetime.now()
        self.dir_path_for_saved_files =  f"data/{time_now.strftime('%m-%d-%Y,%H-%M-%S')}"
        self.last_chechpoint_time = datetime.now()
        self.xp, self.yp = None, None # this is for drawing purposes # TODO: should return to none after the user changes
        self.brush: BRUSH_STATE = BRUSH_STATE.OFF
        with tracker() as trkr:
            time.sleep(3)
            self.imgCanvas = np.zeros((trkr._kinect.color_frame_desc.Height, trkr._kinect.color_frame_desc.Width, 3), np.uint8) # set up the image canvas
            
            while True:
                
                bodies: list[Skeleton]= trkr.get_body_data()
                
                # here we should decide wheather to create a new user for each skeleton or give to an old user
                # right now we will simply create a new user for each skeleton 
                for body in bodies:
                    self.update_players(body)
                

                img = np.zeros((trkr._kinect.color_frame_desc.Height, trkr._kinect.color_frame_desc.Width, 3), np.uint8) # create a black image to draw each player on 

                
                for player in self.players:
                    self.detect_actions(player) # detects players actions
                    ### HERE WE ADD THE HERISTICS OF GIVING THE CONTROLLER OR REMOVING IT
                    self.update_main_player()

                    ### ___ DRAWING ____###
                    # here we draw the players as skeletons we keda
                    trkr.draw_body_bones(img, player.body, color=player.color)# draw the bones of each player
                    self.draw_player_status(img, player) # draw the player status for debugging

                
                self.draw_main_player_indicator(img) # draw an indicator of current main player
                
                self.draw_requesting_players_indicator(img)# draw an indicator for the reqesting players
                    
                img = self.main_player_paint(img) # must return the img as this is not a cv2 simple funciton
                
                cv2.imshow('Clap game', img)
                # saving the game status
                if self.time_to_take_snapshot():
                    self.checkpoint(img) 

                
                if cv2.waitKey(1) == ord('q'):
                    break

                
        cv2.destroyAllWindows()

        self.save_data_to_disk()

    def main_player_paint(self, img):
        """here we add the paint brush to make the game layout"""
        # Constants 
        brusht = 15
        rubbert = 100
        if self.main_user is not None: 
            
            x1, y1 = np.rint(self.main_user.body.HandRight.x).astype(int), np.rint(self.main_user.body.HandRight.y).astype(int)
            x2, y2 = np.rint(self.main_user.body.HandTipRight.x).astype(int), np.rint(self.main_user.body.HandTipRight.y).astype(int)
            if  not all((self.xp, self.yp)): # if xp or yp is None
                self.xp, self.yp=x1, y1
            if self.brush == BRUSH_STATE.OFF: # TODO: this will be changed to gesture closed Hand later
                    # Mode selection Not drawing or moving
                    pass # do not do anything as we do not want to draw yet

            elif self.brush == BRUSH_STATE.DRAWING: # drawing mode
                drawColor = (0, 123, 0)
                cv2.line(img, (self.xp, self.yp), (x1, y1), drawColor, brusht)
                cv2.line(self.imgCanvas, (self.xp, self.yp), (x1, y1), drawColor, brusht)
            elif self.brush == BRUSH_STATE.ERASE: # erase mode
                drawColor = (0, 0, 0)
                cv2.line(img, (self.xp, self.yp), (x1, y1), drawColor, brusht)
                cv2.line(self.imgCanvas, (self.xp, self.yp), (x1, y1), drawColor, brusht)

            self.xp, self.yp = x1, y1 # save this as the new position previous


                
        # update the frame I think
        imgGray = cv2.cvtColor(self.imgCanvas, cv2.COLOR_BGR2GRAY)
        _, imgInv = cv2.threshold(imgGray, 50, 255, cv2.THRESH_BINARY_INV)
        imgInv = cv2.cvtColor(imgInv, cv2.COLOR_GRAY2BGR)
        img = cv2.bitwise_and(img, imgInv)
        img = cv2.bitwise_or(img, self.imgCanvas)
        return img


                
    def draw_main_player_indicator(self, img):
        if self.main_user is not None: # if someone has the controller then we should show him with a status
            cv2.circle(img, center=( int(self.main_user.body.SpineMid.x), int(self.main_user.body.SpineMid.y)), color=(255, 0, 0), radius=50, thickness=-1)
                    
    def draw_requesting_players_indicator(self, img):
        for idx, player in enumerate(self.requesting_players):
            cv2.circle(img, center=( int(player.body.SpineMid.x), int(player.body.SpineMid.y)), color=(0, 0, 255), radius=50, thickness=-1)
            cv2.putText(img, f'{idx+1}', ( int(player.body.SpineMid.x), int(player.body.SpineMid.y)), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 0), 3, cv2.LINE_AA)


    # GAME EVENTS HANDLERS
    @smokesignal.on(GAME_EVENTS.USER_GIVE_CONTROL)
    def event_user_give_control(self):
        # if this user gave controll then 
        if len(self.requesting_players) == 0: # if no one is requesting and the user gave up the controll 
            self.main_user = None
        else:
            self.main_user = self.requesting_players.pop() # make the next in line the main user
            self.xp, self.py = None, None # so that the new user can start drawing from his own position

    @smokesignal.on(GAME_EVENTS.USER_REQUEST_CONTROL)
    def event_user_request_control(self, player:player):
        """event handler for when a user requests the controll"""
       
        # if there is no one to take the controller than he should take it 
        if self.main_user is None or self.main_user == player:
            self.main_user = player
        elif player not in self.requesting_players: # if another player has the controller than it should not give it to him  
            # here we will add this player to the quee of requesting players
            self.requesting_players.append(player) 
            pass # TODO: This should also see if the player who is controlling did some gesture in the time being
            
        pass

    @smokesignal.on(GAME_EVENTS.ADD_BRUSH)
    def event_add_brush(self, player:player):
        """event handler for when the brush should be set"""
        if player == self.main_user:
            self.brush = BRUSH_STATE.DRAWING # allow the user to draw
    @smokesignal.on(GAME_EVENTS.REMOVE_BRUSH)
    def event_add_brush(self, player:player):
        """event handler for when the brush should be off the paper"""
        if player == self.main_user:
            self.brush = BRUSH_STATE.OFF # allow the user to draw
        
        

    def detect_actions(self, player: player):
        if player.doing_gesture(GESTURES.RAISE_RIGHT_HAND):
            smokesignal.emit(GAME_EVENTS.USER_REQUEST_CONTROL, self ,player) # if you need the game instance in the event handler then pass it here
        if player.doing_gesture(GESTURES.RAISE_LEFT_HAND):
            #print('player raised left hand but no signal event was assigned')
            smokesignal.emit(GAME_EVENTS.USER_GIVE_CONTROL, self)
        if player.doing_gesture(GESTURES.OPENING_RIGHT_HAND):
            smokesignal.emit(GAME_EVENTS.REMOVE_BRUSH, self, player)
        if player.doing_gesture(GESTURES.CLOSEING_RIGHT_HAND):
            smokesignal.emit(GAME_EVENTS.ADD_BRUSH, self, player)
    def update_main_player(self):
        """Funciton to update the main player by letting him keep the controller or simply removing it from him based on some crieterias
        """
        pass
                

    def draw_player_status(self, img:np.array, player:player):
        # 
        strings_to_show= [f"ID:", f"Number of claps", f"requesting:{player.doing_gesture(GESTURES.RAISE_RIGHT_HAND)}"]
        pos_of_head_x, pos_of_head_y = int(player.body.Head.x), int(player.body.Head.y)
        
        for idx, string in enumerate(strings_to_show):
            cv2.putText(img, string, (pos_of_head_x,pos_of_head_y-idx*50), cv2.FONT_HERSHEY_SIMPLEX, 2, player.color, 3, cv2.LINE_AA)

        # if the player is main then that player will simply have 
      


    def update_players(self, body:Skeleton):
        _id= id(body) 
        if _id in player.known_skeletons:
            # then we know this skeleton and it should not be added to players as it is already in players
            pass 
        else:
            # add it 
            player.known_skeletons[_id] = player(body)
            self.players.append(player.known_skeletons[_id])

    def checkpoint(self, img:np.array):
        # here we take a snapshot of the system by saving the players array 
        self.players_buffer.append(pickle.dumps(self.players, protocol=pickle.HIGHEST_PROTOCOL)) # save the state of the players array 
        #self.img_buffer.append(img) # save the img that was rendered to be able to play it back 
        filename =f'{self.dir_path_for_saved_files}/image_data.avi'
        if self.video_writer is None:
            height, width, layers = img.shape
            size = (width,height)
            FPS = 1000 / self.CHECKPOINT_MS # fps = 1/ delta_time between frames # iguess
            os.makedirs(os.path.dirname(filename), exist_ok=True) # make the directrory
            self.video_writer = cv2.VideoWriter(filename,cv2.VideoWriter_fourcc(*'MJPG'), 24, size)
            

        
        self.video_writer.write(img)
        
    def time_to_take_snapshot(self):
        miliseconds = (datetime.now() - self.last_chechpoint_time) / timedelta(milliseconds=1)
        if  miliseconds > self.CHECKPOINT_MS : # if enoguh time passed from the last checkpoint then return true
            self.last_chechpoint_time = datetime.now()
            return True
        return False

    def save_data_to_disk(self):
        """resposible for saving the buffer data stored to disk
        """        
        # first create a directory to save this to having a name with the date this game was played in
        time_now = datetime.now()
        dir_path = self.dir_path_for_saved_files
        # save the player buffer
        filename = f'{dir_path}/players_data.pickle'
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'wb') as handle:
            pickle.dump(self.players_buffer, handle, protocol=pickle.HIGHEST_PROTOCOL)
        
        # save the img buffer
        # filename =f'{dir_path}/image_data.pickle'
        # os.makedirs(os.path.dirname(filename), exist_ok=True)
        # with open(filename, 'wb') as handle:
        #     pickle.dump(self.img_buffer, handle, protocol=pickle.HIGHEST_PROTOCOL)

        # ? save the img buffer as an cv2 video not a pickle cuz picke is heacy ###
        # img = self.img_buffer[0]
        # height, width, layers = img.shape
        # size = (width,height)
        # FPS = 1000 / self.CHECKPOINT_MS # fps = 1/ delta_time between frames # iguess
        # out = cv2.VideoWriter(filename,cv2.VideoWriter_fourcc(*'DIVX'), 15, size)
        # filename =f'{dir_path}/image_data.avi'
        # ### once you are done with those 
        # for img in self.img_buffer:
            
        #     out.write(img)

        # out.release()
        self.video_writer.release()
            
    
    @staticmethod
    def load_data_from_disk(dir_path:str):
        filename = f'{dir_path}/image_data.avi'
        filename2 = f'{dir_path}/players_data.pickle'
        cap = cv2.VideoCapture(filename)

        with open(filename2, 'rb') as a:
            trkr = tracker()
            player_buffer = pickle.load(a)
            if (cap.isOpened()== False):
                print("Error opening video stream or file")
                return

            
            for players in player_buffer:
                players = pickle.loads(players)
                img = np.zeros((trkr._kinect.color_frame_desc.Height, trkr._kinect.color_frame_desc.Width, 4)) # create a black image to draw each player on 
                
                # draw a recreation of the frame data onto another image
                for player in players:
                    # here we draw the players as skeletons we keda
                    trkr.draw_body_bones(img, player.body, color=player.color)# draw the bones of each player
                # draw the recorded frame data 
                cv2.imshow('recreational video', img) # this is the recreation from the body recorded data
                ret, frame = cap.read() # get the next frame from the video player
                if ret == True:
                    cv2.imshow('Actuall recorded Video',frame) # this is the actuall recorded video
                else:
                    print('no frame here')
                time.sleep(clapGame.CHECKPOINT_MS/1000) # to make it the same as the time it was recorded in
                if cv2.waitKey(1) == ord('q'):
                    break
            cv2.destroyAllWindows()
            cap.release()

if __name__=='__main__':
    c= clapGame() # record a game for senario
    #clapGame.load_data_from_disk(c.dir_path_for_saved_files) # replay the game in 2 ways
    # 1 is playing the frames of the game with all the UI
    # 2 simply using the data from the 
    print('finished')