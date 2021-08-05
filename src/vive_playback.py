#!/usr/bin/python3

import rospy
import rosbag
from std_msgs.msg import String

import socket
import time
import os
import sys
import textwrap
from pathlib import Path


class Args:
    def __init__(self, bag_file, input_topic, out_port, mode): 
        self.bag_file = bag_file
        self.input_topic = input_topic
        self.out_port = out_port
        self.mode = mode
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self.bag = None
        self.topic_sub = None


def printHelpMessage():
    msg = textwrap.dedent("""
        Command-line usage: vive_playback.py [mode]

        You may run this program as a stand-alone script or through a launch file.
        If a launch file is used, you may specify a number of ROS parameters, otherwise
        default values will be used.

        The mode parameter should be one of \"record\" or \"play\".
    """)

    print(msg)

def getArgs():
    bag_file = rospy.get_param("~bag_file", "vive_input.bag")
    input_topic = rospy.get_param("~input_topic", "/vive_input/raw_string")
    out_port = rospy.get_param("~out_port", 8081)

    arg_list = rospy.myargv(sys.argv)
    if len(arg_list) != 2:
        printHelpMessage()
        return None

    mode = arg_list[1]
    if mode != "record" and mode != "play":
        printHelpMessage()
        return None

    args = Args(bag_file, input_topic, out_port, mode)

    return args


def publishViveInput(args: Args):
    bag_file = Path(args.bag_file)
    bag_name = os.path.basename(args.bag_file)
    if not bag_file.is_file():
        print("ERROR: .bag file \"{}\" does not exist.".format(bag_name))
        return

    try:
        args.bag = rosbag.Bag(args.bag_file)
    except:
        print("ERROR: Could not open .bag file:", bag_name)
        return

    # start = time.time()

    address = ('', args.out_port)
    prev_tstamp = None
    prev_real = None
    for topic, msg, tstamp in args.bag.read_messages(args.input_topic):
        if rospy.is_shutdown():
            break
        
        if prev_tstamp is None:
            prev_real = time.time()
            prev_tstamp = tstamp
        
        # Adjust for time elapsed during send and print
        real_diff = time.time() - prev_real
        sleep_rate = tstamp - prev_tstamp
        sleep_rate = sleep_rate.to_sec() - real_diff
        if sleep_rate > 0:
            time.sleep(sleep_rate)

        prev_real = time.time()
        prev_tstamp = tstamp

        args.socket.sendto(msg.data.encode('utf-8'), address)
        print(msg.data)
        

    # end = time.time()
    # print("Time elapsed: ", end - start)

    args.socket.close()


def recordViveInput(msg, args: Args):
    cur_str = String()
    cur_str.data = msg.data

    try:
        args.bag.write(args.input_topic, cur_str)
    except:
        print("Could not write message \"{}\" to bag.".format(msg.data))

def initRecordingSubscriber(args: Args):
    print("~~~ Record mode selected ~~~")
    
    bag_file = Path(args.bag_file)
    if bag_file.is_file():
        response = None
        while response != "yes" and response != "y" and response != "no" and response != "n":
            response = input(".bag file already exists. Would you like to clear it? ").strip().lower()
        if response == "yes" or response == "y":
            print("File cleared. Now recording...")
            args.bag = rosbag.Bag(args.bag_file, 'w')
        else:
            print("Appending new data to file...")
            args.bag = rosbag.Bag(args.bag_file, 'a')
    else:
        print(".bag file created. Now recording...")
        args.bag = rosbag.Bag(args.bag_file, 'w')

    args.topic_sub = rospy.Subscriber(args.input_topic, String, recordViveInput, args)
    
    rospy.spin()
    args.bag.close()


if __name__ == '__main__':
    rospy.init_node("vive_playback", anonymous=True)
    args = getArgs()

    if args is None:
        exit()

    if args.mode == "record":
        initRecordingSubscriber(args)
    else: # Mode is "play"
        publishViveInput(args)

    
