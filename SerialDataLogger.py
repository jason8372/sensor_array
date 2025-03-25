import serial
import csv
import time
from datetime import datetime
import os

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray, Int32
from geometry_msgs.msg import PoseStamped, Point
from visualization_msgs.msg import Marker

from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy, HistoryPolicy

from rclpy.executors import MultiThreadedExecutor


import numpy as np

class SensorClassifier(Node):
    def __init__(self):
        super().__init__('sensor_classifier')

        qos_profile = QoSProfile(
            
            depth=20,  # Buffer up to 10 messages (or another depth suitable for your application)
            reliability=ReliabilityPolicy.BEST_EFFORT,  # Best Effort reliability
            durability=DurabilityPolicy.VOLATILE,  # Volatile durability
        )

        # qos_profile = QoSProfile(
        #     reliability=QoSReliabilityPolicy.BEST_EFFORT,
        #     durability=QoSDurabilityPolicy.VOLATILE
        # )
        self.ser = None
        self.curr_time = time.time()
        self.time = 0
        # Publishers
        self.marker_pub = self.create_publisher(Marker, '/sensor/visualization', 10)
        self.sensor_pub = self.create_publisher(Float32MultiArray, '/sensor/sensor_data', 10)
        self.classification_pub = self.create_publisher(Int32, '/sensor/classification_result', qos_profile=qos_profile)
        self.point_pub = self.create_publisher(PoseStamped, '/sensor/x', 10)

        # Subscriber for pose
        self.pose_sub = self.create_subscription(PoseStamped, '/mavros/local_position/pose', self.pose_callback,  qos_profile=qos_profile)

        self.sensor_msg = Float32MultiArray()
        self.classification_msg = Int32()

        # Initialize serial port
        self.reading_list = []
        self.current_pose = None
        self.current_sensor_data = [0.0, 0.0, 0.0, 0.0]  # Default sensor values
        self.classification_result = [-1]

        self.published_points = []

        # Set up file path for logging
        start_time = datetime.now()
        self.filename = start_time.strftime("data/serial_data_log_%Y-%m-%d_%H-%M-%S.csv")

        self.serial_port = "/dev/ttyUSB0"
        self.baudrate = 115200
        # Initialize CSV file if not exists
        self.init_csv()

        # Set up ROS 2 rate (10Hz loop)
        # try:
        #     self.ser = serial.Serial(self.serial_port, self.baudrate, timeout=1)
        #     print("connected to {self.serial_port}")
        # except serial.SerialException as e:
        #     print("Error connecting")
        #     exit(1)

        self.timer = self.create_timer(0.1, self.read_serial_data)

        
    def init_csv(self):
        if not os.path.exists(self.filename):
            with open(self.filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["timestamp", "sensor1", "sensor2", "sensor3", "sensor4", "classification_result", "x", "y", "z"])
            self.get_logger().info(f"CSV file created: {self.filename}")

    def pose_callback(self,msg):
        current_time = time.time()
        self.get_logger().info(f"Pose updated at {current_time}: x={msg.pose.position.x}, y={msg.pose.position.y}, z={msg.pose.position.z}")

        self.current_pose = msg
    
    def save_to_csv(self,classification):
        
        self.time = time.time() - self.curr_time

        if self.current_pose:
            x = self.current_pose.pose.position.x
            y = self.current_pose.pose.position.y
            z = self.current_pose.pose.position.z
        else:
            x,y,z = -1,-1,-1
        if classification[0]:

            with open(self.filename,'a',newline='') as f:
                # if(classfication):
                writer = csv.writer(f)
                writer.writerow(([self.time] + classification[:4] + [classification[4], x, y, z]))

    def create_marker(self, position, marker_id):
        marker = Marker()
        marker.header.frame_id = "world"  # Set the frame_id to world (or base_link, depending on your setup)
        marker.header.stamp = self.get_clock().now().to_msg()

        marker.ns = "sensor_points"
        marker.id = marker_id  # Unique ID for each marker
        marker.type = Marker.SPHERE
        marker.action = Marker.ADD

        marker.pose.position.x = position.x
        marker.pose.position.y = position.y
        marker.pose.position.z = position.z

        marker.scale.x = 0.1  # Size of the sphere
        marker.scale.y = 0.1
        marker.scale.z = 0.1

        marker.color.a = 1.0  # Set alpha to 1 (fully visible)
        marker.color.r = 1.0  # Red color
        marker.color.g = 0.0
        marker.color.b = 0.0

        return marker
    
    def read_serial_data(self):
        if not self.ser:
            try:
                self.ser = serial.Serial(self.serial_port, self.baudrate, timeout=1)
                self.get_logger().info(f"Connected to serial port {self.serial_port}")
            except serial.SerialException as e:
                self.get_logger().error(f"Error connecting to serial port: {e}")
                return

        try:
            if self.ser.in_waiting > 0:  # Non-blocking check if data is available
                line = self.ser.readline().decode('utf-8').strip()

                if line.startswith("D:"):
                    raw_data = line[2:]  # Remove "D:" prefix
                    fields = raw_data.split(',')

                    self.sensor_msg.data = [float(i) for i in fields[:4]]
                    self.classification_msg.data = int(fields[4])

                    # Publish sensor data and classification result
                    self.sensor_pub.publish(self.sensor_msg)
                    self.classification_pub.publish(self.classification_msg)

                    if self.classification_msg.data == 1 and self.current_pose:
                        # Publish classification points
                        point_msg = PoseStamped()
                        point_msg.pose.position.x = self.current_pose.pose.position.x
                        point_msg.pose.position.y= self.current_pose.pose.position.y
                        point_msg.pose.position.z= self.current_pose.pose.position.z
                        self.point_pub.publish(point_msg)

                        marker_id = len(self.published_points)  # Generate a new unique marker ID
                        marker = self.create_marker(self.current_pose.pose.position, marker_id)

                        # Store the marker for future reference (optional)
                        self.published_points.append(marker)

                        # Publish the marker
                        self.marker_pub.publish(marker)
                        self.get_logger().info(f"Published marker with ID {marker_id} at x={marker.pose.position.x}, y={marker.pose.position.y}, z={marker.pose.position.z}")

                        

                    if len(fields) == 5:
                        self.save_to_csv(fields)
                    else:
                        self.get_logger().warning(f"⚠️ Invalid data format: {line}")
        except Exception as e:
            self.get_logger().error(f"Error reading from serial port: {e}")
            if self.ser:
                self.ser.close()
                self.ser = None
        
        
        

            # finally:
            #     ser.close()
def main(args = None):
    rclpy.init(args=args)
    sensor_classfier = SensorClassifier()

    try:
        rclpy.spin(sensor_classfier)
        # executor = MultiThreadedExecutor()
        # executor.add_node(sensor_classfier)
        # executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        sensor_classfier.ser.close()
        sensor_classfier.destroy_node()
        rclpy.shutdown()
if __name__ == '__main__':
    main()

        