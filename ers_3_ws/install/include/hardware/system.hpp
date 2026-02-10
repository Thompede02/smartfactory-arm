#pragma once

#include <string>
#include <vector>
#include <memory>
#include <unordered_map>

#include "rclcpp/rclcpp.hpp"
#include "rclcpp_lifecycle/node_interfaces/lifecycle_node_interface.hpp"

#include "hardware_interface/system_interface.hpp"
#include "hardware_interface/hardware_info.hpp"
#include "hardware_interface/types/hardware_interface_type_values.hpp"
#include "hardware_interface/types/hardware_interface_return_values.hpp"

#include "std_msgs/msg/float64_multi_array.hpp"
#include "sensor_msgs/msg/joint_state.hpp"

namespace ros2_control_ers6
{

using CallbackReturn =
  rclcpp_lifecycle::node_interfaces::LifecycleNodeInterface::CallbackReturn;

class RobotSystemHardware : public hardware_interface::SystemInterface
{
public:
  CallbackReturn on_init(
    const hardware_interface::HardwareInfo & info) override;

  CallbackReturn on_configure(
    const rclcpp_lifecycle::State & previous_state) override;

  CallbackReturn on_activate(
    const rclcpp_lifecycle::State & previous_state) override;

  CallbackReturn on_deactivate(
    const rclcpp_lifecycle::State & previous_state) override;

  hardware_interface::return_type read(
    const rclcpp::Time & time,
    const rclcpp::Duration & period) override;

  hardware_interface::return_type write(
    const rclcpp::Time & time,
    const rclcpp::Duration & period) override;

  std::vector<hardware_interface::StateInterface> export_state_interfaces() override;
  std::vector<hardware_interface::CommandInterface> export_command_interfaces() override;

private:
  // Keep same joint names as URDF
  std::vector<std::string> joint_names_;
  std::vector<double> pos_;
  std::vector<double> vel_;
  std::vector<double> cmd_;

  // Variable for Encoder state
  std::vector<double> enc_pos_;
  std::vector<bool>   enc_ok_;

  // Name from the index
  std::unordered_map<std::string, std::size_t> name_to_index_;

  // internal ROS Node
  rclcpp::Node::SharedPtr node_;

  // Publish commands to servo_node
  rclcpp::Publisher<std_msgs::msg::Float64MultiArray>::SharedPtr servo_pub_;

  // Subscribe encoder Jointstates from the encoder node
  rclcpp::Subscription<sensor_msgs::msg::JointState>::SharedPtr encoder_sub_;

  // Executor to process encoder callbacks
  std::shared_ptr<rclcpp::executors::SingleThreadedExecutor> executor_;

  // Separate callback function (simpler than a big lambda)
  void encoder_callback(const sensor_msgs::msg::JointState::SharedPtr msg);
};

}  // namespace ros2_control_ers6
