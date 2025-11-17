from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node
import os

def generate_launch_description():
    urdf_file_path = os.path.join(
        get_package_share_directory('ers6_description'),
        'urdf',
        'ers6.urdf'
    )

    with open(urdf_file_path, 'r') as infp:
        robot_description_content = infp.read()

    return LaunchDescription([
        # Launch robot_state_publisher to read the URDF directly
        # Robot State Publisher
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            parameters=[{'robot_description': robot_description_content}]
        ),

        # Joint State Publisher GUI
        Node(
            package='joint_state_publisher_gui',
            executable='joint_state_publisher_gui',
            name='joint_state_publisher_gui'
        ),

        # Launch RViz2 to visualize the robot
        Node(
            package="rviz2",
            executable="rviz2",
            name="rviz2",
            output="screen",
            arguments=[]
        )
    ])
