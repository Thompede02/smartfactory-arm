from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():
    hw_pkg = get_package_share_directory('hardware')
    ctrl_pkg = get_package_share_directory('control')

    urdf_path = os.path.join(hw_pkg, 'urdf', 'ers6_robot.urdf')
    controllers_yaml = os.path.join(ctrl_pkg, 'config', 'ers6_controller.yaml')
    arm_params_yaml = os.path.join(ctrl_pkg, 'config', 'ers6_arm_controller.params.yaml')

    with open(urdf_path, 'r') as f:
        robot_desc = f.read()

    return LaunchDescription([
        Node(package='robot_state_publisher', executable='robot_state_publisher',
             parameters=[{'robot_description': robot_desc}], output='screen'),

        Node(package='controller_manager', executable='ros2_control_node',
             parameters=[{'robot_description': robot_desc}, controllers_yaml],
             output='screen'),

        Node(package='controller_manager', executable='spawner',
             arguments=['joint_state_broadcaster'], output='screen'),

        Node(package='controller_manager', executable='spawner',
             arguments=['ers6_arm_controller', '--param-file', arm_params_yaml],
             output='screen'),
    ])
