from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution, TextSubstitution, Command, FindExecutable
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from launch.conditions import IfCondition

def generate_launch_description():
    use_rviz = LaunchConfiguration("rviz")
    urdf_path_arg = LaunchConfiguration("urdf_path")

    declare_rviz = DeclareLaunchArgument("rviz", default_value="true")
    declare_urdf = DeclareLaunchArgument(
        "urdf_path",
        default_value=PathJoinSubstitution(
            [FindPackageShare("ers6_description"), "urdf", "ers6_demo.urdf"]  # <-- FAKE controller URDF
        ),
        description="URDF file for demo (uses mock_components/GenericSystem).",
    )

    # Core MoveIt config files
    moveit_cfg = FindPackageShare("ers6_moveit_config")
    srdf_file = PathJoinSubstitution([moveit_cfg, "config", "ers6.srdf"])
    kinematics_yaml = PathJoinSubstitution([moveit_cfg, "config", "kinematics.yaml"])
    ompl_yaml = PathJoinSubstitution([moveit_cfg, "config", "ompl_planning.yaml"])
    limits_yaml = PathJoinSubstitution([moveit_cfg, "config", "joint_limits.yaml"])
    controllers_yaml = PathJoinSubstitution([moveit_cfg, "config", "moveit_controllers.yaml"])
    ros2_ctrl_yaml = PathJoinSubstitution([moveit_cfg, "config", "ros2_controllers.yaml"])

    robot_description = {
        "robot_description": Command([FindExecutable(name="cat"), TextSubstitution(text=" "), urdf_path_arg])
    }
    robot_description_semantic = {
        "robot_description_semantic": Command([FindExecutable(name="cat"), TextSubstitution(text=" "), srdf_file])
    }

    # Robot State Publisher
    rsp = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="screen",
        parameters=[robot_description],
    )

    # ros2_control (fake) + spawners
    ctrl_mgr = Node(
        package="controller_manager",
        executable="ros2_control_node",
        output="screen",
        parameters=[robot_description, ros2_ctrl_yaml],
    )
    spawner_js = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster"],
        output="screen",
    )
    spawner_jtc = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_trajectory_controller"],
        output="screen",
    )

    # Move Group (explicitly pass ALL configs, including kinematics + controllers)
    move_group = Node(
        package="moveit_ros_move_group",
        executable="move_group",
        output="screen",
        parameters=[
            robot_description,
            robot_description_semantic,
            ompl_yaml,
            kinematics_yaml,          # <-- fixes "No kinematics plugins defined"
            limits_yaml,
            controllers_yaml,         # <-- fixes "No controller_names specified"
            {"planning_pipelines": ["ompl"]},
            {"moveit_controller_manager": "moveit_simple_controller_manager/MoveItSimpleControllerManager"},
        ],
    )

    # RViz
    rviz = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="screen",
        parameters=[robot_description, robot_description_semantic],
        condition=IfCondition(use_rviz),
    )

    return LaunchDescription([
        declare_rviz,
        declare_urdf,
        rsp,
        ctrl_mgr,
        spawner_js,
        spawner_jtc,
        move_group,
        rviz,
    ])
