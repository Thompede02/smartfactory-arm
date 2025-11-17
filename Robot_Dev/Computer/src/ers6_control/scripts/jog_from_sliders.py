#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint

class SuperSimpleJog(Node):
    def __init__(self):
        super().__init__('super_simple_jog')

        # Controller topic
        self.controller_topic = '/ers6_trajectory_controller/joint_trajectory'
        # Joint names in same order as controller
        self.joint_names = [
            'base_link_to_a5','a5_to_a4','a4_to_a3','a3_to_a2','a2_to_a1','a1_to_a0'
        ]

        # Publisher to controller
        self.pub = self.create_publisher(JointTrajectory, self.controller_topic, 10)
        # Subscribe to GUI slider joint states
        self.sub = self.create_subscription(JointState, '/slider_joint_states', self.cb, 10)

        self.get_logger().info('SuperSimpleJog running. Move sliders to move robot.')

    def cb(self, msg):
        # Assume msg.position order is the same as self.joint_names
        traj = JointTrajectory()
        traj.joint_names = self.joint_names

        pt = JointTrajectoryPoint()
        pt.positions = msg.position  # take positions directly from GUI
        pt.time_from_start.sec = 0
        pt.time_from_start.nanosec = 300_000_000  # 0.3s so controller accepts

        traj.points.append(pt)
        self.pub.publish(traj)

def main():
    rclpy.init()
    node = SuperSimpleJog()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
