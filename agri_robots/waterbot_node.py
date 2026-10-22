import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped, Twist
import json
import os

class WaterBot(Node):
    def __init__(self):
        super().__init__('waterbot_node')
        self.publisher_ = self.create_publisher(PoseStamped, '/goal_pose', 10)
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.timer = self.create_timer(25.0, self.go_to_next)
        self.index = 0
        self.anomaly_file = os.path.expanduser("~/anomalies.json")
        self.waiting_for_anomalies_file = False
        self.wait_timer = None
        self.rotation_timer = None
        self.rotation_end_time = None
        self.coords = []

        self.load_coords()

    def load_coords(self):
        try:
            with open(self.anomaly_file) as f:
                self.coords = [p for p in json.load(f)['moisture_anomalies'] if p['moisture'] < 30]
        except FileNotFoundError:
            self.coords = []
            self.waiting_for_anomalies_file = True
            self.get_logger().warn(f"{self.anomaly_file} not found; waiting for navigator output.")
            return False

        self.waiting_for_anomalies_file = False
        self.get_logger().info(f"Loaded {len(self.coords)} moisture anomaly points.")
        return True

    def now_seconds(self):
        seconds, nanoseconds = self.get_clock().now().seconds_nanoseconds()
        return seconds + nanoseconds / 1e9

    def go_to_next(self):
        if self.waiting_for_anomalies_file and not self.load_coords():
            return

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
        self.timer.cancel()
        self.wait_timer = self.create_timer(25.0, self.start_rotation)

    def start_rotation(self):
        if self.wait_timer is not None:
            self.wait_timer.cancel()
            self.wait_timer = None

        self.get_logger().info("Performing 2 rotations")
        self.rotation_end_time = self.now_seconds() + 53.0
        self.rotation_timer = self.create_timer(0.1, self.publish_rotation)
        self.publish_rotation()

    def publish_rotation(self):
        twist = Twist()
        if self.now_seconds() < self.rotation_end_time:
            twist.angular.z = 0.5
            self.cmd_vel_pub.publish(twist)
            return

        twist.angular.z = 0.0
        self.cmd_vel_pub.publish(twist)
        if self.rotation_timer is not None:
            self.rotation_timer.cancel()
            self.rotation_timer = None
        self.index += 1
        self.go_to_next()

def main(args=None):
    rclpy.init(args=args)
    node = WaterBot()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

