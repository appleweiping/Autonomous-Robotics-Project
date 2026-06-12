import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped, Twist
import json
import os

class SprayBot(Node):
    def __init__(self):
        super().__init__('spraybot_node')
        self.publisher_ = self.create_publisher(PoseStamped, '/goal_pose', 10)
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.timer = self.create_timer(25.0, self.go_to_next)
        self.index = 0
        self.wait_timer = None
        self.shake_timer = None
        self.shake_end_time = None
        self.shake_direction = 1

        with open(os.path.expanduser("~/anomalies.json")) as f:
            self.coords = [p for p in json.load(f)['ph_anomalies'] if p['ph'] < 5.5 or p['ph'] > 7.5]

        self.get_logger().info(f"Loaded {len(self.coords)} pH anomaly points.")

    def now_seconds(self):
        seconds, nanoseconds = self.get_clock().now().seconds_nanoseconds()
        return seconds + nanoseconds / 1e9

    def go_to_next(self):
        if self.index >= len(self.coords):
            self.get_logger().info("Spraybot finished all tasks.")
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
        self.wait_timer = self.create_timer(25.0, self.start_shaking)

    def start_shaking(self):
        if self.wait_timer is not None:
            self.wait_timer.cancel()
            self.wait_timer = None

        self.get_logger().info("Shaking for 5 seconds")
        self.shake_end_time = self.now_seconds() + 5.0
        self.shake_direction = 1
        self.shake_timer = self.create_timer(0.5, self.publish_shake)
        self.publish_shake()

    def publish_shake(self):
        twist = Twist()
        if self.now_seconds() < self.shake_end_time:
            twist.angular.z = 0.5 * self.shake_direction
            self.cmd_vel_pub.publish(twist)
            self.shake_direction *= -1
            return

        twist.angular.z = 0.0
        self.cmd_vel_pub.publish(twist)
        if self.shake_timer is not None:
            self.shake_timer.cancel()
            self.shake_timer = None
        self.index += 1
        self.go_to_next()

def main(args=None):
    rclpy.init(args=args)
    node = SprayBot()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

