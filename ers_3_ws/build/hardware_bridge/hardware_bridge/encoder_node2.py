#!/usr/bin/env python3

import os
import math
from math import pi
import yaml

from rclpy import init, spin, shutdown
from rclpy.node import Node
from sensor_msgs.msg import JointState

import board
import busio
from adafruit_tca9548a import TCA9548A
from adafruit_as5600 import AS5600


class EncoderReader(Node):
    def __init__(self):
        Node.__init__(self, "encoder_node")

        # --- Load YAML config ---
        package_dir = os.path.dirname(__file__)
        hardware_config = os.path.join(package_dir, "ers6_hardware.yaml")
        with open(hardware_config) as f:
            config = yaml.safe_load(f)

        # --- I2C + mux ---
        i2c_bus = busio.I2C(board.SCL, board.SDA)  # Initialize I2C communication
        encoder_mux = TCA9548A(i2c_bus, address=0x70) #

        # For each joint with an encoder, store (name, encoder, zero_rad, sign)
        self.joints = []

        for j in config["joints"]:
            name = j["name"]
            mux_channel = j.get("encoder_mux_channel")
            if mux_channel is None:
                # This joint has no encoder (open-loop joint)
                continue

            machine_zero = float(j.get("encoder_zero_deg", 0.0))
            sign = float(j.get("encoder_sign", 1.0))
            zero_rad = machine_zero * pi / 180.0

            try:
                enc = AS5600(encoder_mux[mux_channel])  # AS5600 at default addr 0x36
                self.joints.append((name, enc, zero_rad, sign))

            except Exception as e:
                self.get_logger().warn(
                    f"{name}: no encoder on mux {mux_channel}: {e}"
                )


        # Publisher: joint states from encoders
        self.pub = self.create_publisher(JointState, "/encoder_joint_states", 10)

        self.create_timer(0.05, self.timer_cb) # Publish at 20 Hz

    def timer_cb(self):
        msg = JointState()
        msg.header.stamp = self.get_clock().now().to_msg()

        for name, enc, machine_zero, sign in self.joints:
            # Raw_Counts
            raw = enc.angle              # 0 to 4095
            # Angle_Deg
            deg = raw * 360.0 / 4096.0   # 0 to 360
            #Angle_Rad
            rad = deg * math.pi / 180.0  # 0 to 2π
            #Joint_Angle
            joint_angle = sign * (rad - machine_zero)

            msg.name.append(name)
            msg.position.append(joint_angle)

        self.pub.publish(msg)


def main(args=None):
    init(args=args)
    node = EncoderReader()
    try:
        spin(node)
    except KeyboardInterrupt:
        pass
    shutdown()

if __name__ == "__main__":
    main()
