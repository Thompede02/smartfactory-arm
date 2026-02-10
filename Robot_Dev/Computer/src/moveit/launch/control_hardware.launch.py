import os
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    # Assign package directory
    description_share = get_package_share_directory("description")
    moveit_share = get_package_share_directory("moveit")

    # Files path
    urdf_path = os.path.join(description_share, "urdf", "ers6.urdf")
    srdf_path = os.path.join(moveit_share, "config", "ers6.srdf")

    # Config paths
    kinematics_yaml       = os.path.join(moveit_share, "config", "kinematics.yaml")
    kinematics_rviz_yaml  = os.path.join(moveit_share, "config", "kinematics_rviz.yaml")
    joint_limits_yaml     = os.path.join(moveit_share, "config", "joint_limits.yaml")
    controllers_yaml      = os.path.join(moveit_share, "config", "moveit_controllers.yaml")
    ompl_yaml             = os.path.join(moveit_share, "config", "ompl_planning.yaml")

    # Read URDF
    with open(urdf_path, "r") as f:
        robot_description = f.read()

    with open(srdf_path, "r") as f:
        robot_description_semantic = f.read()

    # MoveIt move_group node
    move_group = Node(
        package="moveit_ros_move_group",
        executable="move_group",
        output="screen",
        parameters=[
            {"robot_description": robot_description},
            {"robot_description_semantic": robot_description_semantic},
            kinematics_yaml,
            joint_limits_yaml,
            controllers_yaml,
            ompl_yaml,
            {
                "planning_pipelines": ["ompl"],
                "moveit_controller_manager":
                    "moveit_simple_controller_manager/MoveItSimpleControllerManager",
            },
        ],
    )

    # Rviz2 with displays
    rviz = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="screen",
        parameters=[
            {"robot_description": robot_description},
            {"robot_description_semantic": robot_description_semantic},
            kinematics_rviz_yaml,
        ],
    )

    return LaunchDescription([
        move_group,
        rviz,
    ])
