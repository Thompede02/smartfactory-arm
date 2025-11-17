# Runs ONLY ros2_control (hardware + controllers). No TF here.
import os
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    control_share = get_package_share_directory('control')
    description_share = get_package_share_directory('ers6_description')

    urdf_path = os.path.join(description_share, 'urdf', 'ers6.urdf')
    main_ctrl_yaml = os.path.join(control_share, 'config', 'ers6_controller.yaml')
    traj_yaml = os.path.join(control_share, 'config', 'ers6_trajectory_controller.yaml')

    with open(urdf_path, 'r') as f:
        robot_description = f.read()

    ros2_control = Node(
        package='controller_manager',
        executable='ros2_control_node',
        output='screen',
        parameters=[
            main_ctrl_yaml,  # declares controller types
            {'robot_description': robot_description},
        ],
    )

    jsb_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['joint_state_broadcaster', '--controller-manager', '/controller_manager'],
        output='screen',
    )

    traj_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=[
            'ers6_trajectory_controller',
            '--controller-manager', '/controller_manager',
            '--param-file', traj_yaml
        ],
        output='screen',
    )

    return LaunchDescription([ros2_control, jsb_spawner, traj_spawner])
