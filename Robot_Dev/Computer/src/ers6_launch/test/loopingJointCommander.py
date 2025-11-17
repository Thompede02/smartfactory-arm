import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64MultiArray
import time

class SimpleJointCommander(Node):
    def __init__(self):
        super().__init__('simple_joint_commander')

        # Replace with your actual topic name
        self.publisher_ = self.create_publisher(Float64MultiArray, '/forward_position_controller/commands', 10)

        # Small delay to ensure publisher is ready
        time.sleep(1)

        # Example: Move to home pose
        home_pose = [0.0, -1.57, 1.57, 0.0, 1.57, 0.0]  # Adjust based on your robot
        self.send_joint_command(home_pose)

        # Wait and send another command
        time.sleep(3)
        target_pose = [0.5, -1.0, 1.0, 0.0, 1.2, 0.5]
        self.send_joint_command(target_pose)

        self.get_logger().info('Sent commands. Shutting down...')
        rclpy.shutdown()

    def send_joint_command(self, joint_positions):
        msg = Float64MultiArray()
        msg.data = joint_positions
        self.publisher_.publish(msg)
        self.get_logger().info(f'Commanded joints: {joint_positions}')

def main(args=None):
    rclpy.init(args=args)
    commander = SimpleJointCommander()
    rclpy.spin(commander)

if __name__ == '__main__':
    main()
