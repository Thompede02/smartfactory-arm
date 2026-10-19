# A readme file for the 7R robot showing steps on how to run and what is intalled dedicated for those wish to recreate the project

This repository is part of a master thesis and contains a ROS 2 Humble based 6R robot stack and is based on the work done by the Johannes (previous student) for his work on developing an affordable 6R robot.

- There are hardware component changes and new structural design. New updates include using PCA9685 servo driver (which was challenging to make it work) instead of ESP32 C3 super mini to improve responsivenes and signal processing.

▶ **YouTube demo :** https://youtu.be/wZwo06CZQSk
▶ **GitHub repository (clone on to a fresh Pi):** https://github.com/raashka143/Rasp_Buckup.git

`-----------------------------------------------------------------------------`
==================== DESCRIPTION OF THE ARCHITECTURE =====================
`-----------------------------------------------------------------------------`

This repository contains a ROS 2 Humble bringup for a **7R educational robot arm** (ERS-7) using:

- **ros2_control** (community framework) for controller orchestration
- This setup is based on the ROS 2 ros2_control architecture (similar structure to official examples), and is a continuation/adaptation of earlier work (Johannes’ previous thesis work), with a key hardware change:
- A custom **C++ `hardware_interface::SystemInterface` plugin** that bridges commands/states

- Two **Python hardware bridge nodes**:
  - `servo_node.py` ==> drives **PCA9685** PWM (servos)
  - `encoder_node.py` ==> reads **AS5600** encoders via **TCA9548A** I²C mux
- **controller_manager** with **joint_state_broadcaster** and a **Joint Trajectory Controller**
- **robot_state_publisher** with URDF from `description`
- **PCA9685 servo driver is used instead of ESP32-C3 boards** which

# =============== Key Topics =============

**Key topics**

- Topic `/servo_target_rad` using standard messages (`std_msgs/Float64MultiArray`)  
  Sent by C++ hardware plugin to the servo node (commands per joint in radians).
- Topic `/encoder_joint_states`as (`sensor_msgs/JointState`)  
  Published by the encoder node to the C++ hardware plugin (measured joint positions).

**Read/Write logic (C++ hardware plugin)**

- `write()` publishes `cmd_[]` to `/servo_target_rad` and moves the robot
- `read()` updates `pos_[]` from encoders if available otherwise uses the commanded position as fallback (open-loop joints) and used to visualize robot state using /jont_states

# =============== Installed Libraries and tools =============

- Python nodes use Adafruit Blinka + CircuitPython drivers:
  - `adafruit-blinka` (enables CircuitPython) `board and busio provided by Adafruit Blinka`
  - `adafruit-circuitpython-pca9685` (PCA9685 driver) `Example in the code {self.pca = PCA9685(i2c, address=0x40)}`
  - `adafruit-circuitpython-tca9548a` (mux driver) `Example in code {encoder_mux = TCA9548A(i2c_bus, address=0x70)}`
  - `adafruit-circuitpython-as5600` (AS5600 driver) `Example in the code {AS5600(encoder_mux[mux_channel]}`

`---------------------------------------------------------------------------`
===================== RUNNING THE SYSTEM ON PI ============================
`---------------------------------------------------------------------------`

# Connect to a local network: The Raspberyy Pi is installed with a network manager (UI) and can be accesed with the following codes:

1. $ nmcli -p device show wlan0 `shows currents wifi ip`
2. $ nmcli dev wifi list `Shows a list of availbale network`
3. $ nmcli dev wifi connect "SSID" password "PASSWORD" `Connect to a network`
4. $ ip a show wlan0 `Show given ip address`
5. $ ping -c 4 <pi_ip_address> `Ping Test from a dev machine`
6. $ ip a show wlan0 `Confirm the connection`
7. $ ip r
   # This section shows how to run the system on the Raspberry Pi sitting on the robot (it has libraries installed)
   - The main ROS 2 workspace is **`ers_3_ws`**

## Follow the following steps to ensure running the system:

# Step A: On the Pi Source ROS + workspace:

    1. $ cd ~/Rasp_Buckup/ers_3_ws
    2. $ source /opt/ros/humble/setup.bash
    3. $ source ~/Rasp_Buckup/ers_3_ws/install/setup.bash

# Make sure the robot is placed around its neutral position before the launch

# Step B: Launch everything:

    4. $ ros2 launch control control.launch.py

# This should startup all the nodes and the system should show a clean loading with no errors

# If errors shows we can diagnose by first re-building the system:

    1. $ cd ~/Rasp_Buckup/ers_3_ws
    2. $ rm -rf build install log
    3. $ colcon build --merge-install --symlink-install
    4. $ source ~/Rasp_Buckup/ers_3_ws/install/setup.bash
    5. $ ros2 launch control control.launch.py

# If stil erros show up we can clone a fresh new workspace from Github and repeat above step:

    - $ git clone https://github.com/raashka143/Rasp_Buckup.git

# After succesfull initialization of the system the following nodes are actively running in the background:

    1. controller_manager (ros2_control_node)
    2. joint_state_broadcaster spawner
    3. TrajectoryController spawner
    4. robot_state_publisher
    5. hardware_bridge/servo_node
    6. hardware_bridge/encoder_node

# Verify nodes are availble on the private network:

    1. $ ros2 node list (This should print available nodes)
    2. $ ros2 control list_controllers (This should print controller states)

# Step C: Now we may move the robot by bypassing MoveIt and still get a trajectory motion by sending commands to the TrajectoryController:

    $ ros2 topic pub --once /TrajectoryController/joint_trajectory trajectory_msgs/msg/JointTrajectory "{

    joint_names: ['Joint_1','Joint_2','Joint_3','Joint_4','Joint_5','Joint_6'],
    points: [

    {positions: [0.0,0.0,0.0,0.0,0.0,0.0], time_from_start: {sec: 3}}
    ]
    }"

# Step D: Try changing position values (values are in radians) and hit enter the robot should respond accordingly

`-----------------------------------------------------------------------------------------`
========== CONTROLL THE ROBOT FROM A DEVMACHINE (MOVEIT AND RVIZ INTEGRATION) ============
`-----------------------------------------------------------------------------------------`

With the system running on the Pi MoveIt gives advanced control algarithm like planning and executing and can be cotroll with the interactive UI marker.

# The following are steps necessary for controlling the robot with MoveIt and visulaizing the motion on Rviz using URDF.

# Step A: On the Dev machine Source ROS + workspace:

    1. $ cd ~/Rasp_Buckup/Robot_Dev/Computer
    2. $ source /opt/ros/humble/setup.bash
    3. $ source ~/Rasp_Buckup/Robot_Dev/Computer/install/setup.bash

# Step B: Launch everything:

    1. $ ros2 launch moveit control_hardware.launch.py

`------------------------------------------------------------------------------`
================= NEW RASPBERRY PI (INSTALL ALL FROM SCRATCH) =================
`------------------------------------------------------------------------------`

## follow the ROS2 Humble installation from source on the official website

# Install I2C tools:

sudo apt install -y i2c-tools
ls -l /dev/i2c-1
i2cdetect -y 1 `This prints available i2C devices mainly 0x40 and 0x70`

# Install ROS tools

sudo apt install -y \
 ros-humble-ros-base \
 ros-humble-ros2-control \
 ros-humble-ros2-controllers \
 ros-humble-controller-manager \
 ros-humble-joint-trajectory-controller \
 ros-humble-joint-state-broadcaster \
 ros-humble-robot-state-publisher

## Install Build tools:

sudo apt install -y python3-colcon-common-extensions python3-rosdep git build-essential cmake
sudo rosdep init || true
rosdep update

## Install Python libraries:

sudo pip3 install pyyaml
sudo pip3 install adafruit-blinka
sudo pip3 install adafruit-circuitpython-pca9685
sudo pip3 install adafruit-circuitpython-tca9548a
sudo pip3 install adafruit-circuitpython-as5600

# Make workspace and clone project:

mkdir -p ~/Rasp_Buckup/ers_3_ws/src
cd ~/Rasp_Buckup/ers_3_ws/src
git clone https://github.com/raashka143/Rasp_Buckup.git .

# Follow steps on how to run the system

`-----------------------------------------------------------------------------`
=================== INSTALL PROCEDURE ON DEVMACHINE ===================
`-----------------------------------------------------------------------------`

# The dev machine requires move_group (moveIt 2) and rviz2 (motion planning plugin) to be installed

# Install basic tools:

sudo apt install -y \
 build-essential cmake git \
 python3-pip \
 python3-colcon-common-extensions \
 python3-rosdep \
 python3-vcstool

# Install moveIt_humble

    $ sudo apt install -y ros-humble-moveit

# Install ros2_controllers and controllers:

    $ sudo apt install -y ros-humble-ros2-control ros-humble-ros2-controllers
    $ sudo apt install -y ros-humble-moveit-kinematics

# Install run time toools:

    sudo apt install -y \
    ros-humble-rviz2 \
    ros-humble-robot-state-publisher \
    ros-humble-joint-state-publisher \
    ros-humble-joint-state-publisher-gui \
    ros-humble-xacro \
    ros-humble-controller-manager

# Build workspace and run:

    $ cd ~/Rasp_Buckup/Robot_Dev/Computer
    $ source /opt/ros/humble/setup.bash

    $ rosdep install --from-paths src --ignore-src -r -y
    $ colcon build --symlink-install
    $ colcon build --merge-install --symlink-install
    $ source /opt/ros/humble/setup.bash
    $ source ~/Rasp_Buckup/Robot_Dev/Computer/install/setup.bash

# Before launching make the PI and the devmchine in the same ROS_DOMAIN `run on both devices`

    $ echo 'export ROS_DOMAIN_ID=0' >> ~/.bashrc
    $ source ~/.bashrc

# Run everything and control the robot for the plan and execute UI

    $ ros2 launch moveit control_hardware.launch.py
