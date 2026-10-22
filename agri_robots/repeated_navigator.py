import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
import random
import json
import os

WAYPOINTS = [
    {'x': 1.33, 'y': 0.962},
    {'x': 0.0207, 'y': 0.505},
    {'x': 1.45, 'y': -0.0149}
]

ANOMALY_FILE = os.path.expanduser('~/anomalies.json')
SEEDING_FILE = os.path.expanduser('~/seeding_points.json')

class RepeatedNavigator(Node):
    def __init__(self):
        super().__init__('repeated_navigator')
        self.publisher_ = self.create_publisher(PoseStamped, '/goal_pose', 10)
        self.timer = self.create_timer(35.0, self.send_next_goal)
        self.current_goal_index = 0
        self.pending_goal = None
        self.restart_timer = None
        self.first_run = True
        self.get_logger().info("Repeated Navigator node started.")

    def send_next_goal(self):
        if self.pending_goal is not None:
            self.simulate_sensor(self.pending_goal['x'], self.pending_goal['y'])
            self.current_goal_index += 1
            self.pending_goal = None

        if self.current_goal_index >= len(WAYPOINTS):
            self.get_logger().info("All waypoints visited.")
            self.timer.cancel()
            if not self.first_run:
                self.get_logger().info("Waiting 5 minutes before next navigation cycle.")
                self.restart_timer = self.create_timer(300.0, self.start_new_cycle)
            else:
                self.first_run = False
                self.start_new_cycle()
            return

        goal = WAYPOINTS[self.current_goal_index]
        msg = PoseStamped()
        msg.header.frame_id = 'map'
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.pose.position.x = goal['x']
        msg.pose.position.y = goal['y']
        msg.pose.orientation.w = 1.0

        self.publisher_.publish(msg)
        self.get_logger().info(f"Navigating to ({goal['x']}, {goal['y']})")
        self.pending_goal = goal

    def start_new_cycle(self):
        if self.restart_timer is not None:
            self.restart_timer.cancel()
            self.restart_timer = None

        self.get_logger().info("Resetting anomaly and seeding data for next run.")
        self.current_goal_index = 0
        self.pending_goal = None
        with open(ANOMALY_FILE, 'w') as f:
            json.dump({"ph_anomalies": [], "moisture_anomalies": []}, f, indent=2)
        with open(SEEDING_FILE, 'w') as f:
            json.dump([], f, indent=2)
        self.timer = self.create_timer(35.0, self.send_next_goal)

    def simulate_sensor(self, x, y):
        ph = round(random.uniform(0.0, 14.0), 2)
        moisture = random.randint(0, 100)
        self.get_logger().info(f"Sensor reading at ({x:.2f}, {y:.2f}) → pH={ph}, Moisture={moisture}")

        with open(ANOMALY_FILE, 'r+') as f:
            data = json.load(f)
            if ph < 5.5 or ph > 7.5:
                data['ph_anomalies'].append({'x': x, 'y': y, 'ph': ph})
                self.get_logger().info("pH anomaly logged.")
            if moisture < 30:
                data['moisture_anomalies'].append({'x': x, 'y': y, 'moisture': moisture})
                self.get_logger().info("Moisture anomaly logged.")
            f.seek(0)
            json.dump(data, f, indent=2)
            f.truncate()

        if moisture > 85:
            with open(SEEDING_FILE, 'r+') as f:
                seeding = json.load(f)
                seeding.append({'x': x, 'y': y, 'moisture': moisture})
                f.seek(0)
                json.dump(seeding, f, indent=2)
                f.truncate()
            self.get_logger().info("Added to seeding list (moisture > 85).")

def main(args=None):
    rclpy.init(args=args)
    node = RepeatedNavigator()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

