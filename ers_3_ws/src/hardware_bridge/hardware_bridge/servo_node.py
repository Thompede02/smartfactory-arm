#!/usr/bin/env python3
import os
from math import pi
from ament_index_python.packages import get_package_share_directory
from yaml import safe_load
from rclpy import init, spin, shutdown
from rclpy.node import Node
from std_msgs.msg import Float64MultiArray as JointTargets

import board
import busio
from adafruit_pca9685 import PCA9685


class ServoNode(Node):
    def __init__(self):
        super().__init__("servo_node")
        config = self.load_config()
        joints = config["joints"]
        self.joint_arrays(joints)
        self.setup_hardware()
        self.setup_subscription()

    def load_config(self):
        package_directory = get_package_share_directory("hardware_bridge")
        config_path = os.path.join(package_directory, "config", "ers6_hardware.yaml")
        with open(config_path, "r") as f:
            return safe_load(f)

    def joint_arrays(self, joints):
        self.pca_channels = []
        self.signs = []
        self.scales = []
        self.min_us = []
        self.max_us = []
        self.joint_min = []
        self.joint_max = []

        for j in joints:
            self.pca_channels.append(int(j["servo_channel"]))
            self.min_us.append(float(j.get("servo_min_us", 600.0)))
            self.max_us.append(float(j.get("servo_max_us", 2400.0)))
            self.signs.append(float(j.get("servo_sign", 1.0)))
            self.scales.append(float(j.get("servo_scale", 1.0)))

            self.joint_min.append(float(j.get("joint_min_rad", -pi / 2)))
            self.joint_max.append(float(j.get("joint_max_rad",  pi / 2)))

    def setup_hardware(self):
        i2c = busio.I2C(board.SCL, board.SDA)
        self.pca = PCA9685(i2c, address=0x40)
        self.pca.frequency = 50.0
        self.period_us = 1_000_000.0 / self.pca.frequency

    def setup_subscription(self):
        topic = "/servo_target_rad"
        self.cmd_sub = self.create_subscription(JointTargets, topic, self.cmd_cb, 10)

    # Helper for Radian-Ticks Conversion
    @staticmethod
    def rad_to_ticks(angle_rad, min_angle_rad, max_angle_rad, min_pulse_us, max_pulse_us, period_us):
        safe_rad = max(min_angle_rad, min(max_angle_rad, angle_rad))
        slope = (max_pulse_us - min_pulse_us) / (max_angle_rad - min_angle_rad)
        pulse_us = min_pulse_us + slope * (safe_rad - min_angle_rad)
        ticks = int(pulse_us * 4096.0 / period_us)
        return max(0, min(4095, ticks))

    def cmd_cb(self, msg):
        for joint_index, target_joint_rad in enumerate(msg.data):
            if joint_index >= len(self.pca_channels):
                break  

            # Reading joint variables
            joint_min = self.joint_min[joint_index]
            joint_max = self.joint_max[joint_index]
            sign = self.signs[joint_index]
            scale = self.scales[joint_index]
            us_min = self.min_us[joint_index]
            us_max = self.max_us[joint_index]

            # Clamp into safe angles
            safe_joint = max(joint_min, min(joint_max, float(target_joint_rad)))

            # Map into SERVO radians
            servo_angle = sign * scale * safe_joint

            # Convert joint limits into servo limits
            servo_min = sign * scale * joint_min
            servo_max = sign * scale * joint_max
            min_angle = min(servo_min, servo_max)
            max_angle = max(servo_min, servo_max)

            # Calculate ticks
            ticks = self.rad_to_ticks(servo_angle, min_angle, max_angle, us_min, us_max, self.period_us)

            channel = self.pca_channels[joint_index]
            try:
                self.pca.channels[channel].duty_cycle = ticks << 4
            except OSError as e:
                # A single failed I2C write (e.g. Errno 121 from a power dip)
                # used to crash the node and leave every servo without commands.
                self.get_logger().warn(
                    f"I2C write failed on channel {channel}: {e}",
                    throttle_duration_sec=1.0)


def main(args=None):
    init(args=args)
    node = ServoNode()
    try:
        spin(node)
    except KeyboardInterrupt:
        pass
    shutdown()


if __name__ == "__main__":
    main()
