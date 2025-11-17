from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution, Command, FindExecutable
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    # Launch arguments
    rviz_arg = DeclareLaunchArgument("rviz", default_value="true")
    gui_arg = DeclareLaunchArgument("gui", default_value="false")
    rviz_cfg_arg = DeclareLaunchArgument(
        "rviz_config",
        default_value=PathJoinSubstitution([
            FindPackageShare("ers6_description"), "rviz", "view_robot.rviz"
        ]),
    )

    rviz_enable = LaunchConfiguration("rviz")
    gui_enable = LaunchConfiguration("gui")
    rviz_config = LaunchConfiguration("rviz_config")

    # ✅ Load URDF from the installed ers6_description package
    urdf_file = PathJoinSubstitution([
        FindPackageShare("ers6_description"),
        "urdf",
        "ers6.urdf"
    ])

    robot_description = {
        "robot_description": ParameterValue(
            Command([
                FindExecutable(name="cat"), " ", urdf_file
            ]),
            value_type=str,
        )
    }

    # Nodes
    rsp = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="robot_state_publisher",
        output="screen",
        parameters=[robot_description, {"ignore_timestamp": True}],
    )

    # Remap GUI output from /joint_states -> /slider_joint_states so GUI doesn't fight real joint_states
    jsp_gui = Node(
        package="joint_state_publisher_gui",
        executable="joint_state_publisher_gui",
        name="joint_state_publisher_gui",
        condition=IfCondition(gui_enable),
        remappings=[('/joint_states', '/slider_joint_states')],
    )

    # Launch the jog bridge so GUI slider positions are forwarded to the real controller
    # Only start the jog bridge if gui is enabled (you can remove the condition if you'd like it always running)
    jog_from_sliders = Node(
        package="ers6_control",
        executable="jog_from_sliders.py",
        name="jog_from_sliders",
        output="screen",
        condition=IfCondition(gui_enable),
    )

    rviz2 = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="screen",
        arguments=["-d", rviz_config],
        condition=IfCondition(rviz_enable),
    )

    return LaunchDescription([
        rviz_arg,
        gui_arg,
        rviz_cfg_arg,
        rsp,
        jsp_gui,
        jog_from_sliders,
        rviz2,
    ])
