#!/usr/bin/env python3
from math import pi
import os
from ament_index_python.packages import get_package_share_directory
from yaml import safe_load
from rclpy import init, spin, shutdown
from rclpy.node import Node
from std_msgs.msg import Float64MultiArray as JointTargets
import board
import busio
from adafruit_pca9685 import PCA9685


def clamp(value, low, high):
    return max(low, min(high, value))


class ServoNode(Node):
    def __init__(self):
        super().__init__("servo_node")
        config = self.load_config()
        joints = config["joints"]
        self.load_joint_settings(joints)
        self.setup_hardware()
        self.setup_subscription()

    def load_config(self):
        package_directory = get_package_share_directory("hardware_bridge")
        config_path = os.path.join(package_directory, "config", "ers6_hardware.yaml")
        with open(config_path, "r") as f:
            return safe_load(f)

    def load_joint_settings(self, joints):
        self.pca_channels = []
        self.direction = []
        self.scale = []
        self.pwm_min_us = []
        self.pwm_max_us = []
        self.joint_min_rad = []
        self.joint_max_rad = []

        for j in joints:
            self.pca_channels.append(int(j["servo_channel"]))
            self.pwm_min_us.append(float(j.get("servo_min_us", 600.0)))
            self.pwm_max_us.append(float(j.get("servo_max_us", 2400.0)))
            self.direction.append(float(j.get("servo_sign", 1.0)))
            self.scale.append(float(j.get("servo_scale", 1.0)))

            # Always have safe numeric limits
            self.joint_min_rad.append(float(j.get("joint_min_rad", -pi/2)))
            self.joint_max_rad.append(float(j.get("joint_max_rad",  pi/2)))

    def setup_hardware(self):
        i2c = busio.I2C(board.SCL, board.SDA)
        self.pca = PCA9685(i2c, address=0x40)
        self.pca.frequency = 50.0
        self.period_us = 1_000_000.0 / self.pca.frequency

    def setup_subscription(self):
        # MUST match your ros2_control hardware publisher
        topic = "/servo_target_rad"
        self.cmd_sub = self.create_subscription(JointTargets, topic, self.cmd_cb, 10)

    @staticmethod
    def rad_to_ticks(angle_rad, min_angle_rad, max_angle_rad, min_pulse_us, max_pulse_us, period_us):
        # Safety: avoid division by zero if config is wrong
        if abs(max_angle_rad - min_angle_rad) < 1e-9:
            pulse_us = (min_pulse_us + max_pulse_us) * 0.5
            ticks = int(pulse_us * 4096.0 / period_us)
            return max(0, min(4095, ticks))

        safe_rad = clamp(angle_rad, min_angle_rad, max_angle_rad)
        slope = (max_pulse_us - min_pulse_us) / (max_angle_rad - min_angle_rad)
        pulse_us = min_pulse_us + slope * (safe_rad - min_angle_rad)
        ticks = int(pulse_us * 4096.0 / period_us)
        return max(0, min(4095, ticks))

    def cmd_cb(self, msg):
        for joint_index, requested_joint_rad in enumerate(msg.data):
            if joint_index >= len(self.pca_channels):
                break

            # Read per-joint settings
            joint_min = self.joint_min_rad[joint_index]
            joint_max = self.joint_max_rad[joint_index]
            direction = self.direction[joint_index]
            scale = self.scale[joint_index]
            pwm_min = self.pwm_min_us[joint_index]
            pwm_max = self.pwm_max_us[joint_index]

            # 1) Clamp in joint space
            safe_joint = clamp(float(requested_joint_rad), joint_min, joint_max)

            # 2) Convert to servo space
            servo_target = direction * scale * safe_joint

            # 3) Convert joint limits to servo-space limits (and order them)
            servo_low = min(direction * scale * joint_min, direction * scale * joint_max)
            servo_high = max(direction * scale * joint_min, direction * scale * joint_max)

            # 4) Convert servo angle -> ticks
            ticks = self.rad_to_ticks(servo_target, servo_low, servo_high, pwm_min, pwm_max, self.period_us)

            # 5) Send PWM
            channel = self.pca_channels[joint_index]
            self.pca.channels[channel].duty_cycle = ticks << 4


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
