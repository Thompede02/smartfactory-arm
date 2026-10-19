# Smart factory robot arm (ERS-6)

ROS 2 Humble software for the 6-axis educational robot arm used in the NTNU smart factory (TPK4128 Industrial Mechatronics).

This repository is a fork of [raashka143/Rasp_Buckup](https://github.com/raashka143/Rasp_Buckup), the previous developer's backup of the arm's software. It contains fixes found while bringing the arm back into service (see "Changes from the original" below).

## Repository layout

| Folder | Runs on | Contents |
|---|---|---|
| `ers_3_ws/` | Raspberry Pi on the arm | ros2_control hardware plugin, servo node (PCA9685) and encoder node (AS5600 via TCA9548A), controllers and launch file |
| `Robot_Dev/Computer/` | Student computer (Ubuntu 22.04, VM or WSL) | MoveIt configuration and RViz launch |
| `StepFiles/` | – | CAD of the arm (STL export of the original assembly) |

## Quick start

### On the Raspberry Pi

```bash
cd ~/smartfactory-arm/ers_3_ws
source /opt/ros/humble/setup.bash
colcon build --merge-install --symlink-install
source install/setup.bash
ros2 launch control control.launch.py
```

Place the joints near the zero pose before launching. The arm moves to zero at full servo speed when the controllers start.

### On the student computer (MoveIt + RViz)

```bash
cd ~/smartfactory-arm/Robot_Dev/Computer
source /opt/ros/humble/setup.bash
rosdep install --from-paths src --ignore-src -r -y
colcon build --merge-install --symlink-install
source install/setup.bash
ros2 launch moveit control_hardware.launch.py
```

When ROS runs in a VM (macOS) or WSL (Windows), it cannot discover the Pi directly. A Zenoh bridge (`zenoh-bridge-ros2dds`) on both sides, connected through a `zenohd` router on the host computer, links them. The full step-by-step setup for macOS, Windows and Linux is in the project report.

In RViz: set Fixed Frame to `world`, add the MotionPlanning display, use planning group `manipulator`, and pick a goal state (`HOME`, `READY` or `PICK`).

## Joint and hardware mapping

| Joint | PCA9685 channel | Motion | Encoder |
|---|---|---|---|
| J1 | 0 | Base rotation | – |
| J2 | 1 | Shoulder | – |
| J3 | 2 | Elbow | – |
| J4 | 3 | Forearm rotation | AS5600, mux channel 1 |
| J5 | 4 | Wrist tilt | AS5600, mux channel 0 (disabled, servo broken) |
| J6 | 5 | Wrist rotation | – |
| Gripper | 6 | Open/close | – (not yet in the ROS config) |

## Known limitations

- J5's servo has stripped gears and does not move. Its encoder is disabled in the config until the servo is replaced
- J4's servo only covers about 95 deg, and the joint has an end stop at zero. Its range is limited to 0 to 0.8 rad
- The gripper is not part of the ROS configuration
- `servo_scale` in `ers6_hardware.yaml` has no effect, since it cancels out in the pulse calculation in `servo_node.py`
- No soft start: the arm jumps to the zero pose when the controllers start

## Changes from the original

- Removed committed build output (`build/`, `install/`, `log/`) and macOS metadata files, added `.gitignore`
- MoveIt workspace now builds: CMake only installs folders that exist
- J4 limited to its real range (0 to 0.8 rad) in both URDFs and MoveIt's joint limits
- Encoder mapping corrected: the J4 and J5 encoders were swapped. J4 recalibrated (zero, direction, pulse range)
- `encoder_node.py` wraps the joint angle across the encoder's 360 to 0 deg point
- `servo_node.py` no longer crashes on a single I2C write error
- Corrected paths in `ers_3_ws/README.md`

## Credits

Original hardware and software by Abdirashid Ali (NTNU, 2025), building on earlier work by a previous student on an affordable 6R robot.
