import os
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    control_share = get_package_share_directory('control')
    description_share = get_package_share_directory('description')

    # Paths
    urdf_path = os.path.join(description_share, 'urdf', 'ers6.urdf')
    Main_Controller_Yaml = os.path.join(control_share, 'config', 'Controller.yaml')
    Trajectory_Yaml = os.path.join(control_share, 'config', 'TrajectoryController.yaml')

    # Read URDF
    with open(urdf_path, 'r') as f:
        robot_description = f.read()

    # 1) ros2_control (hardware + controller_manager)
    ros2_control = Node(
        package='controller_manager',
        executable='ros2_control_node',
        output='screen',
        parameters=[
            Main_Controller_Yaml,  # declares controller types
            {'robot_description': robot_description},
        ],
    )

    # 2) Spawner: joint_state_broadcaster
    Joint_State_Broadcaster_Spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=[
            'joint_state_broadcaster',
            '--controller-manager', '/controller_manager',
        ],
        output='screen',
    )

    # 3) Spawner: trajectory controller
    Trajectory_Spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=[
            'TrajectoryController',
            '--controller-manager', '/controller_manager',
            '--param-file', Trajectory_Yaml,
        ],
        output='screen',
    )

    # 4) Robot state publisher (adds /tf + /tf_static)
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{'robot_description': robot_description}],
    )

    Servo_Node = Node(
        package='hardware_bridge',
        executable='servo_node',
        output='screen',
    )

    Encoder_Node = Node(
        package='hardware_bridge',
        executable='encoder_node',
        output='screen',
    )

    return LaunchDescription([
        ros2_control,
        Joint_State_Broadcaster_Spawner,
        Trajectory_Spawner,
        robot_state_publisher,
        Servo_Node,
        Encoder_Node,
    ])
