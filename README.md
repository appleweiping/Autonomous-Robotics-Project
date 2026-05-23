# Autonomous Robotics — Agricultural Robot System

ROS 2 node suite for an autonomous agricultural robot that surveys a field, detects soil anomalies, and dispatches specialized action robots.

---

## System Overview

Five ROS 2 nodes coordinate through shared JSON state files:

| Node | File | Role |
|------|------|------|
| `NavigatorNode` | `navigator_node.py` | Surveys predefined waypoints, logs pH and moisture anomalies |
| `RepeatedNavigator` | `repeated_navigator.py` | Continuous survey loop with anomaly detection |
| `WaterBot` | `waterbot_node.py` | Navigates to moisture-deficient zones (`moisture < 30`) and waters them |
| `SprayBot` | `spraybot_node.py` | Navigates to pH-anomalous zones (`pH < 5.5` or `pH > 7.5`) and sprays corrective agent |
| `SeedBot` | `seedbot_node.py` | Accepts operator-selected coordinates and seeds them |

**Shared state files** (written by navigator, read by action bots):

- `~/anomalies.json` — detected pH and moisture anomaly coordinates
- `~/seeding_points.json` — operator-approved seeding locations

---

## Architecture

```
NavigatorNode / RepeatedNavigator
  ├─ publishes /goal_pose  →  Nav2 stack
  ├─ writes ~/anomalies.json
  └─ writes ~/seeding_points.json

WaterBot   ──reads anomalies.json──▶  navigates to moisture zones
SprayBot   ──reads anomalies.json──▶  navigates to pH zones
SeedBot    ──reads seeding_points.json──▶  navigates to seed zones
```

All nodes publish `geometry_msgs/PoseStamped` to `/goal_pose` and use `geometry_msgs/Twist` on `/cmd_vel` for in-place actuation.

---

## Prerequisites

- ROS 2 (Humble or later)
- Nav2 navigation stack
- Python 3.10+

---

## Running

Launch each node in a separate terminal after sourcing your ROS 2 workspace:

```bash
# Survey the field
ros2 run <package> navigator_node

# Continuous survey
ros2 run <package> repeated_navigator

# Dispatch action bots after anomalies are logged
ros2 run <package> waterbot_node
ros2 run <package> spraybot_node
ros2 run <package> seedbot_node   # prompts for seeding point selection
```

---

## Waypoints

Default survey waypoints (map frame, metres):

| Index | x | y |
|-------|---|---|
| 0 | 1.33 | 0.962 |
| 1 | 0.0207 | 0.505 |
| 2 | 1.45 | −0.0149 |

Edit `WAYPOINTS` in `navigator_node.py` or `repeated_navigator.py` to match your field layout.

---

## Anomaly Thresholds

| Sensor | Threshold | Action |
|--------|-----------|--------|
| Moisture | `< 30` | WaterBot dispatched |
| pH | `< 5.5` or `> 7.5` | SprayBot dispatched |

---

## License

MIT
