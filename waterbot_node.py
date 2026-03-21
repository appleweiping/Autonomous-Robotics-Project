import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped, Twist
import json
import time
import os

class WaterBot(Node):
    def __init__(self):
        super().__init__('waterbot_node')
        self.publisher_ = self.create_publisher(PoseStamped, '/goal_pose', 10)
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.timer = self.create_timer(25.0, self.go_to_next)
        self.index = 0

        with open(os.path.expanduser("~/anomalies.json")) as f:
            self.coords = [p for p in json.load(f)['moisture_anomalies'] if p['moisture'] < 30]

        self.get_logger().info(f"Loaded {len(self.coords)} moisture anomaly points.")

    def go_to_next(self):
        if self.index >= len(self.coords):
            self.get_logger().info("Waterbot finished all tasks.")
            self.timer.cancel()
            return

        pt = self.coords[self.index]
        msg = PoseStamped()
        msg.header.frame_id = 'map'
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.pose.position.x = pt['x']
        msg.pose.position.y = pt['y']
        msg.pose.orientation.w = 1.0
        self.publisher_.publish(msg)
        self.get_logger().info(f"Going to ({pt['x']}, {pt['y']})")
        time.sleep(25)

        self.get_logger().info("Performing 2 rotations")
        twist = Twist()
        twist.angular.z = 0.5
        start_time = self.get_clock().now().seconds_nanoseconds()[0]
        duration = 53

        while self.get_clock().now().seconds_nanoseconds()[0] - start_time < duration:
            self.cmd_vel_pub.publish(twist)
            time.sleep(0.1)

        twist.angular.z = 0.0
        self.cmd_vel_pub.publish(twist)
        self.index += 1

def main(args=None):
    rclpy.init(args=args)
    node = WaterBot()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

