#!/usr/bin/env bash
set -e
source /opt/ros/humble/setup.bash
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/install/setup.bash"
echo "✔ ROS Humble + ~/Robot_Dev/Computer overlay active"
echo "$AMENT_PREFIX_PATH" | tr ':' '\n' | head -n 2
