from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import (
    Command,
    FindExecutable,
    LaunchConfiguration,
    PathJoinSubstitution,
)
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    # -------- Args ----------
    declared = [
        DeclareLaunchArgument("gui", default_value="true",
                              description="Start Joint State Publisher GUI and RViz."),
        DeclareLaunchArgument("use_xacro", default_value="true",
                              description="true: expand xacro at runtime; false: load prebuilt URDF file."),
        DeclareLaunchArgument("rviz", default_value="true",
                              description="Start RViz2"),
        DeclareLaunchArgument(
            "rviz_config",
            default_value=PathJoinSubstitution([
                FindPackageShare("ers6_description"), "rviz", "view_robot.rviz"
            ]),
            description="RViz config path",
        ),
    ]

    gui = LaunchConfiguration("gui")
    use_xacro = LaunchConfiguration("use_xacro")
    rviz_enable = LaunchConfiguration("rviz")
    rviz_config = LaunchConfiguration("rviz_config")

    # -------- Paths ----------
    desc_share = FindPackageShare("ers6_description")
    urdf_dir = PathJoinSubstitution([desc_share, "urdf"])
    xacro_file = PathJoinSubstitution([urdf_dir, "ers6.urdf.xacro"])
    prebuilt_urdf = PathJoinSubstitution([urdf_dir, "ers6.urdf"])

    # -------- robot_description via XACRO (runtime expansion) ----------
    robot_description_from_xacro = {
        "robot_description": ParameterValue(
            Command([PathJoinSubstitution([FindExecutable(name="xacro")]), " ", xacro_file]),
            value_type=str
        )
    }

    # -------- Nodes ----------
    # Joint state publisher: GUI or headless
    jsp_gui = Node(
        package="joint_state_publisher_gui",
        executable="joint_state_publisher_gui",
        condition=IfCondition(gui),
    )
    jsp_headless = Node(
        package="joint_state_publisher",
        executable="joint_state_publisher",
        condition=UnlessCondition(gui),
    )

    # RSP (Option A): use_xacro := true -> feed robot_description (string)
    rsp_from_xacro = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="both",
        parameters=[robot_description_from_xacro],
        condition=IfCondition(use_xacro),
    )

    # RSP (Option B): use_xacro := false -> pass URDF FILE PATH as argv (legacy mode)
    # avoids YAML parsing + 'cat' shell issues entirely
    rsp_from_file = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="both",
        arguments=[prebuilt_urdf],
        condition=UnlessCondition(use_xacro),
    )

    # RViz
    rviz = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="log",
        arguments=["-d", rviz_config],
        condition=IfCondition(rviz_enable),
    )

    return LaunchDescription(declared + [
        jsp_gui,
        jsp_headless,
        rsp_from_xacro,
        rsp_from_file,
        rviz,
    ])
