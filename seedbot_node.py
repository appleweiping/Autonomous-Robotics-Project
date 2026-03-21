import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped, Twist
import json
import time
import os

class SeedBot(Node):
    def __init__(self):
        super().__init__('seedbot_node')
        self.publisher_ = self.create_publisher(PoseStamped, '/goal_pose', 10)
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)

        seeding_file = os.path.expanduser("~/seeding_points.json") # Load seeding points from JSON
        with open(seeding_file, 'r') as f:
            self.all_coords = json.load(f)

        if not self.all_coords:
            self.get_logger().warn("No seeding points available.")
            return

        print("\n Available seeding locations:")
        for i, point in enumerate(self.all_coords):
            print(f"[{i}] x: {point['x']}, y: {point['y']}, moisture: {point['moisture']}")

        indices = input("\nEnter comma-separated indices to seed: ").split(',')
        self.selected_points = [self.all_coords[int(i)] for i in indices if i.strip().isdigit()]
        self.index = 0
        self.timer = self.create_timer(25.0, self.go_to_next)

    def go_to_next(self):
        if self.index >= len(self.selected_points):
            self.get_logger().info("SeedBot finished all selected points.")
            self.timer.cancel()
            return

        pt = self.selected_points[self.index]
        goal = PoseStamped()
        goal.header.frame_id = 'map'
        goal.header.stamp = self.get_clock().now().to_msg()
        goal.pose.position.x = pt['x']
        goal.pose.position.y = pt['y']
        goal.pose.orientation.w = 1.0

        self.publisher_.publish(goal)
        self.get_logger().info(f" Heading to point ({pt['x']:.2f}, {pt['y']:.2f})")
        time.sleep(30)

        self.perform_seeding()
        self.index += 1

    def perform_seeding(self):
        self.get_logger().info(" Seeding at location (3 rotations)")

        twist = Twist()
        twist.angular.z = 0.5
        start_time = self.get_clock().now().seconds_nanoseconds()[0]
        duration = 80

        while self.get_clock().now().seconds_nanoseconds()[0] - start_time < duration:
            self.cmd_vel_pub.publish(twist)
            time.sleep(0.1)

        twist.angular.z = 0.0
        self.cmd_vel_pub.publish(twist)

def main(args=None):
    rclpy.init(args=args)
    node = SeedBot()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

