from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, Command, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.actions import IncludeLaunchDescription
from launch.substitutions import FindExecutable
import os


def generate_launch_description():
    # Configurable arguments
    declared_arguments = [
        DeclareLaunchArgument(
            'rviz_config',
            default_value=PathJoinSubstitution([
                FindPackageShare('ers6_description'),
                'rviz',
                'view_robot.rviz'
            ]),
            description='Path to the RViz config file'
        )
    ]

    # Paths and parameters
    robot_description_content = Command([
        PathJoinSubstitution([FindExecutable(name='xacro')]),
        ' ',
        PathJoinSubstitution([
            FindPackageShare('ers6_description'),
            'urdf',
            'ers6.urdf.xacro'
        ])
    ])
    robot_description = {'robot_description': robot_description_content}

    controller_yaml = PathJoinSubstitution([
        FindPackageShare('ers6_launch'),
        'config',
        'my_robot_controllers.yaml'
    ])

    rviz_config_file = LaunchConfiguration('rviz_config')

    return LaunchDescription(declared_arguments + [

        # Start ros2_control_node
        Node(
            package='controller_manager',
            executable='ros2_control_node',
            parameters=[robot_description, controller_yaml],
            output='screen',
        ),

        # Spawner for joint_state_broadcaster
        Node(
            package='controller_manager',
            executable='spawner',
            arguments=['joint_state_broadcaster'],
            output='screen',
        ),

        # Spawner for joint_trajectory_controller
        Node(
            package='controller_manager',
            executable='spawner',
            arguments=['joint_trajectory_controller'],
            output='screen',
        ),

        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            output='screen',
            parameters=[robot_description]
        ),

        # RViz2
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            output='screen',
            arguments=['-d', rviz_config_file],
            parameters=[robot_description]
        ),
    ])
