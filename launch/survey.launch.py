"""Start the survey robot.

    ros2 launch agri_robots survey.launch.py              # one pass over the waypoints
    ros2 launch agri_robots survey.launch.py repeat:=true # keep surveying, 5 min between passes

The helper robots (waterbot_node, spraybot_node, seedbot_node) are started
separately with `ros2 run` once the survey has written ~/anomalies.json and
~/seeding_points.json. seedbot_node asks which points to seed on stdin, so it
has to run in a terminal.
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    repeat = LaunchConfiguration('repeat')
    return LaunchDescription([
        DeclareLaunchArgument(
            'repeat', default_value='false',
            description='Run repeated_navigator instead of a single pass'),
        Node(package='agri_robots', executable='navigator_node',
             output='screen', condition=UnlessCondition(repeat)),
        Node(package='agri_robots', executable='repeated_navigator',
             output='screen', condition=IfCondition(repeat)),
    ])
