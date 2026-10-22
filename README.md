# Autonomous-Robotics-Project

A small ROS 2 package for a field-care demo: a survey robot drives to a list of waypoints, takes a
soil reading at each one, and writes the problem spots to JSON files that three helper robots
(water, spray, seed) then work through. It was a TU/e team course project; the soil sensor was
never real, so **pH and moisture readings are simulated** with `random`.

Output of one survey run (from CI, `ros:humble-ros-base`, no Nav2 running, so the robot doesn't
actually move; the node only publishes goals):

```text
$ ros2 launch agri_robots survey.launch.py
[INFO] [navigator_node-1]: process started with pid [503]
[navigator_node-1] [INFO] [1792646095.924552463] [navigator_node]: Navigator node initialized
[navigator_node-1] [INFO] [1792646130.906070204] [navigator_node]: Navigating to (1.33, 0.962)
[navigator_node-1] [INFO] [1792646165.905809315] [navigator_node]: Sensor at (1.33, 0.96): pH=10.37, Moisture=70
[navigator_node-1] [INFO] [1792646165.906403891] [navigator_node]: pH anomaly logged
[navigator_node-1] [INFO] [1792646165.907155794] [navigator_node]: Navigating to (0.0207, 0.505)
^C
$ cat ~/anomalies.json
{
  "ph_anomalies": [
    {
      "x": 1.33,
      "y": 0.962,
      "ph": 10.37
    }
  ],
  "moisture_anomalies": []
}
```

## What each node does

All nodes send goals as `geometry_msgs/PoseStamped` on `/goal_pose` (the topic Nav2's BT
navigator listens to) in the `map` frame. They don't wait for Nav2 to report success; they wait
a fixed time instead.

| Executable | Does |
|------------|------|
| `navigator_node` | Visits the three waypoints in `WAYPOINTS`, one every 35 s. On arrival it makes up a reading (pH 0-14, moisture 0-100). pH below 5.5 or above 7.5 goes to `ph_anomalies`, moisture below 30 goes to `moisture_anomalies`, moisture above 85 goes to the seeding list. |
| `repeated_navigator` | Same survey in a loop. Every new pass clears both JSON files. After the first pass it starts the second one straight away; after that it waits 5 minutes between passes. |
| `waterbot_node` | Reads `moisture_anomalies`, drives to each point and turns on the spot (`/cmd_vel`, 0.5 rad/s for 53 s) as a stand-in for watering. Waits for the file if the survey hasn't written it yet. |
| `spraybot_node` | Reads `ph_anomalies`, drives to each point and wiggles left/right for 5 s as a stand-in for spraying. |
| `seedbot_node` | Lists the seeding points, asks on stdin which ones to seed, then visits them and turns on the spot for 80 s. |

The robots share state through two files in the home directory:

- `~/anomalies.json`: `{"ph_anomalies": [{x, y, ph}], "moisture_anomalies": [{x, y, moisture}]}`
- `~/seeding_points.json`: `[{x, y, moisture}]`

The waypoints `(1.33, 0.962)`, `(0.0207, 0.505)` and `(1.45, -0.0149)` are coordinates in the map the
project was run on; edit `WAYPOINTS` in `agri_robots/navigator_node.py` and
`agri_robots/repeated_navigator.py` for your own map.

## Build and run

Needs ROS 2 Humble or Jazzy (CI builds and tests on both).

```bash
mkdir -p ~/ros2_ws/src && cd ~/ros2_ws/src
git clone https://github.com/appleweiping/Autonomous-Robotics-Project.git agri_robots
cd ~/ros2_ws && colcon build --packages-select agri_robots
source install/setup.bash

ros2 launch agri_robots survey.launch.py               # one survey pass
ros2 launch agri_robots survey.launch.py repeat:=true  # keep surveying
```

Then, with a robot (real or simulated) running Nav2 on the same map:

```bash
ros2 run agri_robots waterbot_node
ros2 run agri_robots spraybot_node
ros2 run agri_robots seedbot_node   # interactive: pick points by index
```

The helper nodes publish on the same `/goal_pose` and `/cmd_vel` topics without namespaces, so run
them one at a time on a single robot, or remap the topics if each runs on its own robot.

## Tests

```bash
colcon test --packages-select agri_robots && colcon test-result --verbose
```

`test/test_survey_logging.py` fixes the "sensor" values and checks which file each reading ends up
in. The GitHub Actions workflow also runs the survey launch file for 80 s and checks that the
first reading was logged.

## Limits

- No real sensors: the readings are random, so every run flags different spots.
- Fixed waits instead of Nav2 action feedback: if the robot needs longer than the wait to reach a
  goal, the node moves on anyway.
- "Watering", "spraying" and "seeding" are only rotations of the robot.

## License

MIT, see [LICENSE](LICENSE).
