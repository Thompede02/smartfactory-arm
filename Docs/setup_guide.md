# Setup guide: running the arm with MoveIt and RViz

This guide takes a new user from a laptop and the robot arm to a working RViz window where the arm can be planned and moved with MoveIt. It is written for macOS, Windows and Linux. The guide was mainly written with the AI assistant Claude (Anthropic), and has been verified it by carrying out the steps and correcting them where needed. The macOS procedure has been carried out and verified; the Windows and Linux procedures follow the same structure but have not yet been tested.

Most of the work is one-time setup ([Overview](#overview) to [Step 7](#step-7-install-the-zenoh-router-on-your-computer-one-time)). Once that is done, each session only needs the start-up sequence in [Step 8](#step-8-start-up-sequence-every-session).

## Contents

- [Overview](#overview)
- [What you need](#what-you-need)
- [Step 1: Connect your computer to the Pi](#step-1-connect-your-computer-to-the-pi)
- [Step 2: Power up the arm and log in to the Pi](#step-2-power-up-the-arm-and-log-in-to-the-pi)
- [Step 3: Check the Pi (one-time)](#step-3-check-the-pi-one-time)
- [Step 4: Install Ubuntu 22.04 on your computer (one-time)](#step-4-install-ubuntu-2204-on-your-computer-one-time)
- [Step 5: Install ROS 2 Humble, MoveIt and Zenoh in Ubuntu (one-time)](#step-5-install-ros-2-humble-moveit-and-zenoh-in-ubuntu-one-time)
- [Step 6: Build the MoveIt workspace (one-time)](#step-6-build-the-moveit-workspace-one-time)
- [Step 7: Install the Zenoh router on your computer (one-time)](#step-7-install-the-zenoh-router-on-your-computer-one-time)
- [Step 8: Start-up sequence (every session)](#step-8-start-up-sequence-every-session)
- [Step 9: Plan and move the arm in RViz](#step-9-plan-and-move-the-arm-in-rviz)
- [Step 10: Shutting down](#step-10-shutting-down)

## Overview

The arm is controlled by a Raspberry Pi mounted on the robot. The student's computer is used for planning and visualization:

- **Raspberry Pi (on the arm)** runs the ROS 2 control stack: the hardware interface, the servo and encoder nodes and the trajectory controller. It receives a trajectory and drives the servos.
- **Your computer** runs MoveIt, which plans collision-free motions, and RViz, which shows the robot in 3D and lets you choose where it should go.
- **Zenoh** links the two. ROS 2 cannot find the Pi on its own when it runs inside a virtual machine or WSL, so a small bridge program on each side carries the ROS traffic over one network connection, through a router program on your computer.

```
  Raspberry Pi              Your computer             Ubuntu (VM / WSL)
  robot control stack       Zenoh router (zenohd)     MoveIt + RViz
  Zenoh bridge  ---------->  port 7447   <----------  Zenoh bridge
```

Everything runs ROS 2 Humble on Ubuntu 22.04. On macOS and Windows, Ubuntu runs inside a virtual machine (macOS) or WSL2 (Windows). On Linux, Ubuntu 22.04 can be used directly.

## What you need

- The robot arm with its Raspberry Pi and SD card
- The Raspberry Pi's own USB-C power supply (5.1 V, 3 A). A laptop USB port does not give enough power
- The servo power supply (PA-90W) for the arm
- An Ethernet cable, and a USB-C to Ethernet adapter if your computer has no Ethernet port
- A computer with at least 8 GB RAM and 40 GB free disk space, with internet access over Wi-Fi
- The login for the Pi (user `thomas`). Ask the supervisor for the password

## Step 1: Connect your computer to the Pi

The Pi is connected to your computer with an Ethernet cable. Your computer then shares its Wi-Fi internet connection over the cable. This gives the Pi an IP address and internet access.

**Important:** switch on sharing *before* powering the Pi, since the Pi asks for an address while it boots.

#### macOS

1. Connect the Ethernet cable from the Pi to the Mac
2. *System Settings* → *General* → *Sharing* → click the (i) next to *Internet Sharing*
3. *Share your connection from:* Wi-Fi. *To devices using:* tick the Ethernet adapter (e.g. *AX88179B* or *USB 10/100/1000 LAN*)
4. Click *Done* and switch *Internet Sharing* on

Your Mac's address towards the Pi is `192.168.2.1`.

#### Windows

1. Connect the Ethernet cable from the Pi to the PC
2. *Settings* → *Network & Internet* → *Advanced network settings* → *More network adapter options*
3. Right-click the Wi-Fi adapter → *Properties* → *Sharing*
4. Tick *Allow other network users to connect*, and choose the Ethernet adapter under *Home networking connection*

Your PC's address towards the Pi is `192.168.137.1`.

#### Linux (Ubuntu)

1. Connect the Ethernet cable from the Pi to the computer
2. *Settings* → *Network* → gear icon next to the wired connection → *IPv4*
3. Choose *Shared to other computers* and click *Apply*

Your computer's address towards the Pi is `10.42.0.1`.

## Step 2: Power up the arm and log in to the Pi

1. Place all joints by hand close to the zero pose. When the control stack starts, the arm moves to zero at full servo speed
2. Connect the Pi's own USB-C supply. The red LED should be steady and the green LED should flicker while booting
3. Connect the PA-90W servo supply. The servos stay limp until the control stack is started
4. Wait 1–2 minutes, then open a terminal on your computer (Terminal on macOS and Linux, PowerShell on Windows) and log in:

   ```bash
   ssh thomas@smartfactory-arm.local
   ```

If `smartfactory-arm.local` is not found, the Pi may still be booting, or sharing may have switched off. On macOS the Pi can also be found by scanning the shared network:

```bash
for i in {2..30}; do ping -c 1 -t 1 192.168.2.$i > /dev/null & done; \
  wait; arp -a | grep dc:a6:32
```

Then log in with the IP address shown, e.g. `ssh thomas@192.168.2.2`. If the Mac warns that the host identification has changed, clear the old key first with `ssh-keygen -R 192.168.2.2`.

#### Two users on the Pi

- `thomas`: used to log in and for every command that needs `sudo`
- `msk`: owns the ROS workspace. All ROS commands are run as this user. Switch with `sudo -iu msk` (it asks for `thomas`' password), and go back with `exit`

## Step 3: Check the Pi (one-time)

Do this step once before the first session, and again if the SD card is replaced. If you are unsure whether it has been done, run `zenoh-bridge-ros2dds --version` and `ls ~/smartfactory-arm` on the Pi. If either command fails, go through the step.

#### Hostname and Zenoh bridge (as `thomas`)

```bash
sudo apt update
sudo apt install -y avahi-daemon
sudo hostnamectl set-hostname smartfactory-arm
echo "deb [trusted=yes] https://download.eclipse.org/zenoh/debian-repo/ /" \
  | sudo tee /etc/apt/sources.list.d/zenoh.list
sudo apt update
sudo apt install -y zenoh-bridge-ros2dds
sudo reboot
```

#### Robot software (as `msk`)

The arm's software is kept in the project repository `github.com/Thompede02/smartfactory-arm`. It is a fork of the previous developer's repository with the fixes found during this project (encoder mapping, J4 range, build fixes and more robust nodes). To install or update it on the Pi:

```bash
sudo -iu msk
git clone https://github.com/Thompede02/smartfactory-arm.git ~/smartfactory-arm
cd ~/smartfactory-arm/ers_3_ws
source /opt/ros/humble/setup.bash
colcon build --merge-install --symlink-install
```

To get the latest changes later, run `git pull` in `~/smartfactory-arm` and build again. If git refuses because a file has local changes, undo them with `git checkout -- <file>` first.

## Step 4: Install Ubuntu 22.04 on your computer (one-time)

#### macOS: Ubuntu in UTM (verified)

1. Install UTM from `mac.getutm.app`
2. Download the Ubuntu 22.04 server image. On Apple Silicon (M1/M2/M3/M4) use the ARM64 version:

   ```bash
   cd ~/Downloads
   curl -LO https://cdimage.ubuntu.com/releases/22.04/release/\
   ubuntu-22.04.5-live-server-arm64.iso
   ```

   Only 22.04 works with ROS 2 Humble. Newer images such as 24.04 or 25.10 will not work. On an Intel Mac, use the `amd64` desktop image instead.
3. In UTM: *Create a New Virtual Machine* → *Virtualize* → *Linux*. Choose the ISO, give it 8 GB memory, 4 CPU cores and at least 40 GB disk. Keep the network on *Shared Network*
4. Start the VM and choose *Try or Install Ubuntu Server*. In the installer:
   - *Installer update available*: *Continue without updating*
   - Proxy: leave blank
   - Storage: *Use an entire disk*, and **untick** *Set up this disk as an LVM group*, otherwise only half the disk is used
   - Profile: your name, a server name (e.g. `ros-humble-vm`), a username and a password
   - Ubuntu Pro: *Skip for now*
   - SSH: tick *Install OpenSSH server*
   - Featured snaps: select none
5. When the installation is done, shut down the VM. In UTM, choose *Edit*, clear the ISO from the USB/CD drive, and set *Display* → *Emulated Display Card* to `virtio-ramfb`. Without this the screen often stays black
6. Start the VM and log in. Note the IP address shown in the welcome message (e.g. `192.168.64.5`)
7. From here on, work over SSH from Terminal on the Mac, since the UTM window does not support copy and paste:

   ```bash
   ssh <your-username>@192.168.64.5
   ```

8. Install the desktop, one command at a time:

   ```bash
   sudo apt update && sudo apt upgrade -y
   sudo apt install -y ubuntu-desktop
   sudo reboot
   ```

   When a purple window asks which services to restart, keep the selection and choose *Ok*. If the graphical login does not appear in UTM after the reboot, set *Display* to `virtio-gpu-gl-pci`.

Do *not* accept the offer to upgrade to a newer Ubuntu release (`do-release-upgrade`).

#### Windows: Ubuntu in WSL2 (not yet tested)

1. Open PowerShell as administrator and run:

   ```powershell
   wsl --install -d Ubuntu-22.04
   ```

2. Restart when asked. Open *Ubuntu 22.04* from the Start menu and create a username and password
3. RViz windows are shown through WSLg, which is included in Windows 11 and recent Windows 10 versions. Run `wsl --update` in PowerShell if graphical programs do not open

#### Linux (not yet tested)

If your computer already runs Ubuntu 22.04, use it directly. On another distribution or version, install Ubuntu 22.04 in a virtual machine (e.g. virt-manager or VirtualBox) and follow the macOS steps.

## Step 5: Install ROS 2 Humble, MoveIt and Zenoh in Ubuntu (one-time)

These commands are the same on all three systems and are run inside Ubuntu (the VM on macOS, WSL on Windows, or the Linux computer itself).

```bash
sudo apt install -y software-properties-common curl
sudo add-apt-repository universe -y
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
  -o /usr/share/keyrings/ros-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) \
  signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] \
  http://packages.ros.org/ros2/ubuntu jammy main" \
  | sudo tee /etc/apt/sources.list.d/ros2.list
sudo apt update
sudo apt install -y ros-humble-desktop ros-humble-moveit \
  ros-humble-ros2-control ros-humble-ros2-controllers \
  python3-colcon-common-extensions python3-rosdep git
sudo rosdep init; rosdep update
echo 'source /opt/ros/humble/setup.bash' >> ~/.bashrc
source ~/.bashrc
```

Check that ROS works with `ros2 --help`. Then install the Zenoh bridge:

```bash
echo "deb [trusted=yes] https://download.eclipse.org/zenoh/debian-repo/ /" \
  | sudo tee /etc/apt/sources.list.d/zenoh.list
sudo apt update
sudo apt install -y zenoh-bridge-ros2dds
```

If `apt` reports *Could not get lock*, Ubuntu is installing updates in the background. Wait a few minutes and try again.

## Step 6: Build the MoveIt workspace (one-time)

The MoveIt configuration for the arm is in the `Robot_Dev/Computer` folder of the project repository, with the joint limits already set to match the real arm. Inside Ubuntu:

```bash
git clone https://github.com/Thompede02/smartfactory-arm.git ~/smartfactory-arm
cd ~/smartfactory-arm/Robot_Dev/Computer
rosdep install --from-paths src --ignore-src -r -y
colcon build --merge-install --symlink-install
echo 'source ~/smartfactory-arm/Robot_Dev/Computer/install/setup.bash' \
  >> ~/.bashrc
```

The build should end with `Summary: 3 packages finished`.

## Step 7: Install the Zenoh router on your computer (one-time)

The router runs on the computer itself, not inside Ubuntu, since both the Pi and Ubuntu can reach the computer but not each other.

#### macOS (verified)

```bash
brew tap eclipse-zenoh/homebrew-zenoh
brew trust eclipse-zenoh/zenoh
brew install zenoh
```

The `brew trust` line is needed because newer Homebrew versions refuse formulas from third-party taps until they are trusted.

#### Windows (not yet tested)

1. Download the Windows version of `zenohd` (`x86_64-pc-windows-msvc` zip) from the Zenoh releases on GitHub, and unpack it
2. Open port 7447 in the firewall (PowerShell as administrator):

   ```powershell
   New-NetFirewallRule -DisplayName "Zenoh" -Direction Inbound `
     -LocalPort 7447 -Protocol TCP -Action Allow
   ```

#### Linux (not yet tested)

When Ubuntu 22.04 runs directly on the computer, Zenoh is usually not needed, since ROS finds the Pi on its own over the shared network. Test this first in Step 8. If it does not work, install `zenohd` from the same apt repository as the bridge (`sudo apt install zenohd`).

Use the same Zenoh version everywhere. Check with:

```bash
zenohd --version
zenoh-bridge-ros2dds --version
```

## Step 8: Start-up sequence (every session)

Step 3 must have been done on the Pi before the first session. Follow this order every time. On macOS you end up with five terminal windows: two on the Pi (control stack and bridge), one for `zenohd` on the Mac, and two in the VM (bridge, and commands). The addresses depend on your system:

| System | Pi bridge connects to | Ubuntu bridge connects to |
|---|---|---|
| macOS | `tcp/192.168.2.1:7447` | `tcp/192.168.64.1:7447` |
| Windows | `tcp/192.168.137.1:7447` | `tcp/<host IP>:7447`, where host IP is found with `ip route show default \| awk '{print $3}'` in WSL |
| Linux (native) | Not needed if `ros2 topic list` already shows the Pi's topics | Not needed |

1. **Hardware:** joints near zero, sharing on, Pi power, servo power (Steps 1 and 2)
2. **Pi, terminal 1:** start the control stack

   ```bash
   ssh thomas@smartfactory-arm.local
   sudo -iu msk
   cd ~/smartfactory-arm/ers_3_ws
   source /opt/ros/humble/setup.bash
   source install/setup.bash
   ros2 launch control control.launch.py
   ```

   Wait for `Configured and activated TrajectoryController`. Keep this terminal open.
3. **Your computer:** start the router (macOS and Linux: `zenohd`; Windows: `zenohd.exe`). Allow incoming connections if asked
4. **Pi, terminal 2:** start the Pi's bridge (as `msk`, the same user as the ROS nodes):

   ```bash
   ssh thomas@smartfactory-arm.local
   sudo -iu msk
   source /opt/ros/humble/setup.bash
   zenoh-bridge-ros2dds -e tcp/192.168.2.1:7447
   ```

   (Use the address for your system from the table.) ROS must be sourced first. The bridge reads `ROS_DISTRO` to choose the message format, and without it, it assumes ROS Iron. Topics then still appear, but MoveIt's requests are dropped with *received invalid request … (less than 20 bytes)*
5. **Ubuntu, terminal 1:** start the Ubuntu bridge, also with ROS sourced:

   ```bash
   source /opt/ros/humble/setup.bash
   zenoh-bridge-ros2dds -e tcp/192.168.64.1:7447
   ```

6. **Ubuntu, terminal 2:** check the link:

   ```bash
   ros2 daemon stop
   ros2 topic list
   ros2 action list
   ```

   `ros2 daemon stop` clears the list of topics cached from earlier attempts. The topic list should include `/joint_states` and `/TrajectoryController/joint_trajectory`, and the action list `/TrajectoryController/follow_joint_trajectory`. If the topic list only shows `/parameter_events` and `/rosout`, the link is not working (see Troubleshooting). Finally, check that joint states arrive and that every joint is inside its limits (J4: 0 to 0.8 rad):

   ```bash
   ros2 topic echo /joint_states --once
   ```

7. **Ubuntu, terminal 2:** start MoveIt and RViz:

   ```bash
   ros2 launch moveit control_hardware.launch.py
   ```

   On macOS, run this in a terminal inside the VM's desktop (not over SSH), since RViz needs the VM's screen. Errors from MoveIt (for example why a plan failed) are printed in this terminal, not in RViz.

If a bridge or the Pi's control stack is restarted while MoveIt is running, restart MoveIt as well. Otherwise it keeps planning from the last joint state it received, which may be wrong.

## Step 9: Plan and move the arm in RViz

RViz opens with an empty view the first time:

1. In the *Displays* panel, under *Global Options*, set *Fixed Frame* to `world`
2. Click *Add* at the bottom of the panel, choose `moveit_ros_visualization` → *MotionPlanning*, and click *OK*. The robot model appears
3. In the MotionPlanning panel, open the *Planning* tab and check that *Planning Group* is `manipulator`. Check that the model's pose matches the real arm, which shows that joint states arrive from the Pi
4. Set *Velocity Scaling* and *Accel. Scaling* to 0.1 for the first runs
5. Set *Start State* to `<current>`. Under *Goal State*, choose one of the predefined poses `HOME`, `READY` or `PICK`, or drag the arrows and rings at the end of the arm to a new position. Start with `READY`; `PICK` turns J2 by 90° and loads the shoulder servo the most
6. Click *Plan*. The planned motion is shown as an animation in RViz, and the real arm stays still
7. Click *Execute*. The trajectory is sent to the arm, and the real arm follows it

If RViz hangs on *Planning…* after an execution, the previous trajectory was aborted on the Pi but the result did not reach MoveIt. Click *Stop* in RViz or restart MoveIt. Save the layout with *File* → *Save Config As*, so it does not have to be set up again.

Start with small motions and keep a hand near the servo power supply the first times. J5 currently has a broken servo and will not follow the plan, and the gripper cannot be controlled from MoveIt yet.

If RViz crashes or shows a black window, start it with software rendering:

```bash
export LIBGL_ALWAYS_SOFTWARE=1
ros2 launch moveit control_hardware.launch.py
```

#### Moving the arm without MoveIt

Joint positions are given in radians, in the order J1–J6. Limits are ±1.57 rad, except J4 which is limited to 0 to 0.8 rad. Example, moving J3 down and back, from a second terminal on the Pi:

```bash
ros2 topic pub --once /TrajectoryController/joint_trajectory \
  trajectory_msgs/msg/JointTrajectory "{
  joint_names: ['Joint_1','Joint_2','Joint_3','Joint_4','Joint_5','Joint_6'],
  points: [
    {positions: [0.0,0.0,-1.57,0.0,0.0,0.0], time_from_start: {sec: 4}},
    {positions: [0.0,0.0,-1.57,0.0,0.0,0.0], time_from_start: {sec: 6}},
    {positions: [0.0,0.0,0.0,0.0,0.0,0.0],   time_from_start: {sec: 10}}
  ]}"
```

Encoder readings for J4 and J5 are shown with `ros2 topic echo /encoder_joint_states`.

## Step 10: Shutting down

1. Use RViz to send the arm to `HOME`
2. Support the arm by hand and disconnect the servo power supply. Stopping ROS alone does not release the servos, since the PCA9685 keeps sending the last signal
3. Stop MoveIt, the bridges and `zenohd` with Ctrl+C
4. On the Pi: stop the control stack with Ctrl+C, type `exit` to go back to `thomas`, then run `sudo shutdown now`
5. Wait until the Pi's green LED stops flickering before unplugging its power. Pulling the power while the Pi is running can damage the SD card
