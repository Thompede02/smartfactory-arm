from launch import LaunchDescription
from launch.actions import LogInfo
from launch.substitutions import Command, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from launch.substitutions import FindExecutable

def generate_launch_description():
    xacro_file = PathJoinSubstitution([
        FindPackageShare("ers6_description"),
        "urdf",
        "ers6.urdf.xacro"
    ])

    robot_description_content = Command([
        PathJoinSubstitution([FindExecutable(name="xacro")]),
        " ",
        xacro_file
    ])

    robot_state_publisher_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="robot_state_publisher",
        output="screen",
        parameters=[{"robot_description": robot_description_content}]
    )

    return LaunchDescription([
        robot_state_publisher_node
    ])
