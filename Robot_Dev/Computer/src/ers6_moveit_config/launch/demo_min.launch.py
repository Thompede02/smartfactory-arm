from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import (
    LaunchConfiguration,
    PathJoinSubstitution,
    TextSubstitution,
    Command,
    FindExecutable,
)
from launch.conditions import IfCondition
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    # Args
    use_rviz = LaunchConfiguration("rviz")
    urdf_path_arg = LaunchConfiguration("urdf_path")

    declare_rviz = DeclareLaunchArgument("rviz", default_value="true")

    # ✅ NOW POINTING TO REAL HARDWARE URDF (ers6.urdf)
    declare_urdf = DeclareLaunchArgument(
        "urdf_path",
        default_value=PathJoinSubstitution(
            [FindPackageShare("ers6_description"), "urdf", "ers6.urdf"]
        ),
        description="URDF for REAL ERS6 hardware (ros2_control_ers6/RobotSystemHardware).",
    )

    # Paths
    moveit_cfg = FindPackageShare("ers6_moveit_config")
    srdf_file = PathJoinSubstitution([moveit_cfg, "config", "ers6.srdf"])
    kinematics_yaml = PathJoinSubstitution([moveit_cfg, "config", "kinematics.yaml"])
    limits_yaml = PathJoinSubstitution([moveit_cfg, "config", "joint_limits.yaml"])
    controllers_yaml = PathJoinSubstitution([moveit_cfg, "config", "moveit_controllers.yaml"])
    ros2_ctrl_yaml = PathJoinSubstitution([moveit_cfg, "config", "ros2_controllers.yaml"])
    ompl_yaml = PathJoinSubstitution([moveit_cfg, "config", "ompl_planning.yaml"])
    kinematics_rviz_yaml = PathJoinSubstitution(
        [moveit_cfg, "config", "kinematics_rviz.yaml"]
    )

    # Descriptions (URDF + SRDF)
    robot_description = {
        "robot_description": ParameterValue(
            Command([FindExecutable(name="cat"), TextSubstitution(text=" "), urdf_path_arg]),
            value_type=str,
        )
    }
    robot_description_semantic = {
        "robot_description_semantic": ParameterValue(
            Command([FindExecutable(name="cat"), TextSubstitution(text=" "), srdf_file]),
            value_type=str,
        )
    }

    # Node: robot_state_publisher
    rsp = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="screen",
        parameters=[robot_description],
    )

    # Node: ros2_control with YOUR hardware plugin from ers6.urdf
    ros2_control_node = Node(
        package="controller_manager",
        executable="ros2_control_node",
        output="screen",
        parameters=[robot_description, ros2_ctrl_yaml],
    )

    # Spawners: controllers
    spawner_js = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster"],
        output="screen",
    )

    spawner_traj = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_trajectory_controller"],
        output="screen",
    )

    # Node: MoveIt move_group
    move_group = Node(
        package="moveit_ros_move_group",
        executable="move_group",
        output="screen",
        parameters=[
            robot_description,
            robot_description_semantic,
            kinematics_yaml,
            limits_yaml,
            controllers_yaml,
            ompl_yaml,
            {"planning_pipelines": ["ompl"]},
            {
                "moveit_controller_manager": (
                    "moveit_simple_controller_manager/MoveItSimpleControllerManager"
                )
            },
        ],
    )

    # Node: RViz2 with MoveIt panel + kinematics_rviz.yaml
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
            ros2_control_node,
            spawner_js,
            spawner_traj,
            move_group,
            rviz,
        ]
    )
