#!/usr/bin/env python
import roslib
import sys
import rospy
import cv2 as cv
import numpy as np
from std_msgs.msg import String
from sensor_msgs.msg import CompressedImage
from cv_bridge import CvBridge, CvBridgeError
from tesla.msg import obstacleData

class image_converter:

  def __init__(self):
    self.camera_name = rospy.get_param("~camera_name","csi_cam_0")
    self.topic_name = rospy.get_param("~topic_name","object_tracking")
    self.tracker_type = rospy.get_param("~tracker_type","MOSSE")  

    self.bridge = CvBridge()
    self.image_sub = rospy.Subscriber(self.camera_name+"/image_raw/compressed",CompressedImage,self.callback)
    self.image_pub = rospy.Publisher(self.topic_name+"/compressed",CompressedImage,queue_size=10)

    #Corey Edit
    #===============================
    print("Setting up publisher for obstacles")
    self.obstacle_pub = rospy.Publisher("obstacles", obstacleData, queue_size=10)
    #===============================

def callback(self,data):
    try:
      frame = self.bridge.compressed_imgmsg_to_cv2(data, "bgr8")
    except CvBridgeError as e:
      print(e)

    frame_gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
    frame_gray = cv.equalizeHist(frame_gray)

    faces = self.face_cascade.detectMultiScale(frame_gray,1.2, 5,0,(50,50))
    for (x,y,w,h) in faces:
        frame = cv.rectangle(frame, (x, y),(x+w, y+h), ( 0, 255, 0), 2)

    cv.imshow("Face detection", frame)
    cv.waitKey(3)

    try:
      self.image_pub.publish(self.bridge.cv2_to_compressed_imgmsg(frame))
    except CvBridgeError as e:
      print(e)

def main(args):
  print("Initializeing node")
  rospy.init_node('image_converter', anonymous=True)
  print("Done!")
  ic = image_converter()

  #Corey Edit
  #===============================
  i = 1
  rate =  rospy.Rate(1) # 1hz
  while(i < 4):
    rate.sleep()
    message = obstacleData()
    message.id = i
    message.strData = "Camera script message"
    message.x = 209
    message.y = 209
    message.z = 0


    print("Publishing a message")
    ic.obstacle_pub.publish(message)
    i += 1
  #===============================

  try:
    rospy.spin()
  except KeyboardInterrupt:
    print("Shutting down")
  cv.destroyAllWindows()

if __name__ == '__main__':
    main(sys.argv)

