
import time
import cv2
import numpy as np
def capture_and_save_depth_video(tracker, file_path='output.avi'):
    with tracker as tracker:
        time.sleep(3)

        # Create an object to read
        # from camera
        video = tracker.show_depth_image(return_img=True)

        # We need to set resolutions.
        # so, convert them from float to integer.
        frame_width = int(video.shape[1])
        frame_height = int(video.shape[0])

        size = (frame_width, frame_height)
        print('frame size', size)
        # Below VideoWriter object will create
        # a frame of above defined The output
        # is stored in 'filename.avi' file.
        result = cv2.VideoWriter(file_path,
                                cv2.VideoWriter_fourcc(*'MJPG'),
                                60, size, False)
            
        while(True):
            frame= tracker.show_depth_image(return_img=True)
            ret, frame = (frame is not None), frame
            #print(ret, frame)
            if ret == True:
                #frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
                # Write the frame into the
                # file 'filename.avi'
                frame = cv2.cvtColor(frame,cv2.COLOR_GRAY2BGR)
                frame = cv2.cvtColor(frame,cv2.COLOR_RGB2GRAY)

                result.write(frame)

                # Display the frame
                # saved in the file
                cv2.imshow('Frame', frame)

                # Press q on keyboard
                # to stop the process
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

            # Break the loop
            else:
                break

        # When everything done, release
        # the video capture and video
        # write objects
        result.release()
            
        # Closes all the frames
        cv2.destroyAllWindows()

        print("The video was successfully saved")

if __name__ == '__main__':
  save_depth_data()

