#!/usr/bin/env python
# encoding: utf-8
import rospy
import sys
import argparse
from jetson_inference import detectNet
from jetson_utils import videoSource, videoOutput, Log
from tesla.msg import obstacleData
from camfunctions import widthFinder, distanceFinder

class Camtest:    

    def __init__(self):
        # Initialize node
        rospy.init_node('Cam_Test')
        print('Cam_Test node is online')

        # Do Stuff
        # Attach to Publish to 'our_obstacle'

        self.obstacle_pub = rospy.Publisher("our_obstacles", obstacleData, queue_size=1)

        # parse the command line
        parser = argparse.ArgumentParser(description="Locate objects in a live camera stream using an object detection DNN.", 
                                         formatter_class=argparse.RawTextHelpFormatter, epilog=detectNet.Usage() + videoSource.Usage() + videoOutput.Usage() + Log.Usage())

        parser.add_argument("input", type=str, default="csi://0", nargs='?', help="URI of the input stream")
        parser.add_argument("output", type=str, default="", nargs='?', help="URI of the output stream")
        parser.add_argument("--network", type=str, default="ssd-mobilenet-v2", help="pre-trained model to load (see below for options)")
        parser.add_argument("--overlay", type=str, default="box,labels,conf", help="detection overlay flags (e.g. --overlay=box,labels,conf)\nvalid combinations are:  'box', 'labels', 'conf', 'none'")
        parser.add_argument("--threshold", type=float, default=0.5, help="minimum detection threshold to use") 

        try:
            args = parser.parse_known_args()[0]
        except:
            print("")
            parser.print_help()
            sys.exit(0)

        # create video sources and outputs
        input = videoSource("csi://0")
        output = videoOutput(args.output, argv=sys.argv)
            
        # load the object detection network

        # net = detectNet(args.network, sys.argv, args.threshold)

        # note: to hard-code the paths to load a model, the following API can be used:
        net = detectNet(model="../../../../Documents/jetson-inference/python/training/detection/ssd/models/obstacle/ssd-mobilenet.onnx", labels="../../../../Documents/jetson-inference/python/training/detection/ssd/models/obstacle/labels.txt", 
                    input_blob="input_0", output_cvg="scores", output_bbox="boxes", 
                    threshold=args.threshold)
        
        rate = rospy.Rate(1) # 1 image per second

        # process frames until EOS or the user exits
        while not rospy.is_shutdown():
            rate.sleep() # Sleep between frames

            # capture the next image
            img = input.Capture()

            if img is None: # timeout
                continue  
            
            # detect objects in the image (with overlay)
            detections = net.Detect(img, overlay=args.overlay)

            # print the detections
            print("detected {:d} objects in image".format(len(detections)))

            for detection in detections:
                print(detection)
                # Build the data struct
                # The coordinates for the bounding box is in pixels 
                # The Camera is flipped.
                # create obstacle data custom struct

                ob = obstacleData()

                # Class ID is the label of the class.
                # class 0 is not_obstacle, class 1 is obstacle
                if detection.ClassID == 1:

                    # Take the bottom pixel and judge how close the obstacle is in cm
                    # find the calculate the bottom co-ordinates of the box.

                    # find the calculate the co-ordinates of the box.
                    half_width = detection.Width * 0.5


                    botpix = detection.Bottom
                    bl_coord = botpix - half_width
                    br_coord = botpix + half_width

                    widthCM = widthFinder(bl_coord, br_coord)
                    distanceCM = distanceFinder(botpix)
                    print("Proccessed obstacle: distanceCM: {:f}, widthCM: {:f}")

                    #Build it!
                    ob.bot_left = bl_coord
                    ob.bot_right = br_coord
                    ob.classification = detection.ClassID
                    ob.distance_from_bumper = distanceCM
                    ob.width_cm = widthCM
                    
                    #Ship it!
                    self.obstacle_pub.publish(ob)



            # render the image
            output.Render(img)

            # update the title bar
            output.SetStatus("{:s} | Network {:.0f} FPS".format(args.network, net.GetNetworkFPS()))

            # print out performance info
            net.PrintProfilerTimes()

            # exit on input/output EOS
            if not input.IsStreaming() or not output.IsStreaming():
                break

        # Destructor
    def cancel(self):
        print('Closing Node')

    

if __name__ == '__main__':
    Camtest()
