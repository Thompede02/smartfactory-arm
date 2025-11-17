from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import (
    LaunchConfiguration,
    PathJoinSubstitution,
    TextSubstitution,
    Command,
    FindExecutable,
)
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    # ----------------- Launch arguments -----------------
    use_rviz = LaunchConfiguration("rviz")
    urdf_path_arg = LaunchConfiguration("urdf_path")

    declare_rviz = DeclareLaunchArgument(
        "rviz",
        default_value="true",
        description="Start RViz2 with MoveIt motion planning panel",
    )

    declare_urdf = DeclareLaunchArgument(
        "urdf_path",
        # 👉 REAL robot URDF here (ers6.urdf)
        default_value=PathJoinSubstitution(
            [FindPackageShare("ers6_description"), "urdf", "ers6.urdf"]
        ),
        description="Real robot URDF (with ros2_control tag, but no local hardware on PC).",
    )

    # ----------------- Common paths -----------------
    moveit_cfg = FindPackageShare("ers6_moveit_config")

    srdf_file = PathJoinSubstitution([moveit_cfg, "config", "ers6.srdf"])
    kinematics_yaml = PathJoinSubstitution([moveit_cfg, "config", "kinematics.yaml"])
    limits_yaml = PathJoinSubstitution([moveit_cfg, "config", "joint_limits.yaml"])
    controllers_yaml = PathJoinSubstitution(
        [moveit_cfg, "config", "moveit_controllers.yaml"]
    )
    ompl_yaml = PathJoinSubstitution([moveit_cfg, "config", "ompl_planning.yaml"])
    kinematics_rviz_yaml = PathJoinSubstitution(
        [moveit_cfg, "config", "kinematics_rviz.yaml"]
    )

    # ----------------- Descriptions -----------------
    robot_description = {
        "robot_description": ParameterValue(
            Command(
                [
                    FindExecutable(name="cat"),
                    TextSubstitution(text=" "),
                    urdf_path_arg,
                ]
            ),
            value_type=str,
        )
    }

    robot_description_semantic = {
        "robot_description_semantic": ParameterValue(
            Command(
                [
                    FindExecutable(name="cat"),
                    TextSubstitution(text=" "),
                    srdf_file,
                ]
            ),
            value_type=str,
        )
    }

    # ----------------- Nodes on the PC -----------------

    # 1) Robot State Publisher
    # Uses /joint_states topic (coming from the Pi)
    rsp = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="screen",
        parameters=[robot_description],
    )

    # ❌ NO ros2_control_node here.
    # All ros2_control + controllers are running on the Pi.

    # 2) MoveIt move_group (planning + execution)
    move_group = Node(
        package="moveit_ros_move_group",
        executable="move_group",
        output="screen",
        parameters=[
            robot_description,
            robot_description_semantic,
            kinematics_yaml,
            limits_yaml,
            controllers_yaml,  # <-- uses the file we just fixed
            ompl_yaml,
            {"planning_pipelines": ["ompl"]},
            {
                "moveit_controller_manager": (
                    "moveit_simple_controller_manager/MoveItSimpleControllerManager"
                )
            },
        ],
    )

    # 3) RViz2 with MoveIt plugin
    rviz = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="screen",
        parameters=[
            robot_description,
            robot_description_semantic,
            kinematics_rviz_yaml,
        ],
        condition=IfCondition(use_rviz),
    )

    return LaunchDescription(
        [
            declare_rviz,
            declare_urdf,
            rsp,
            move_group,
            rviz,
        ]
    )
