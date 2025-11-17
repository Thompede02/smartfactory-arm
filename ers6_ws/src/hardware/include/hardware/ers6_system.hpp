#pragma once

#include <string>
#include <unordered_map>
#include <vector>
#include <array>

#include "hardware_interface/system_interface.hpp"
#include "hardware_interface/types/hardware_interface_return_values.hpp"
#include "hardware_interface/types/hardware_interface_type_values.hpp"
#include "hardware_interface/handle.hpp"
#include "hardware_interface/hardware_info.hpp"
#include "rclcpp_lifecycle/lifecycle_node.hpp"

#include "hardware/comms.hpp"
#include "hardware/actuator.hpp"

namespace ros2_control_ers6
{
using CallbackReturn = rclcpp_lifecycle::node_interfaces::LifecycleNodeInterface::CallbackReturn;

class RobotSystemHardware : public hardware_interface::SystemInterface
{
public:
  RCLCPP_SHARED_PTR_DEFINITIONS(RobotSystemHardware)

  CallbackReturn on_init(const hardware_interface::HardwareInfo & info) override;
  CallbackReturn on_configure(const rclcpp_lifecycle::State & previous_state) override;
  CallbackReturn on_activate(const rclcpp_lifecycle::State & previous_state) override;
  CallbackReturn on_deactivate(const rclcpp_lifecycle::State & previous_state) override;

  hardware_interface::return_type read(const rclcpp::Time & time, const rclcpp::Duration & period) override;
  hardware_interface::return_type write(const rclcpp::Time & time, const rclcpp::Duration & period) override;

  std::vector<hardware_interface::StateInterface> export_state_interfaces() override;
  std::vector<hardware_interface::CommandInterface> export_command_interfaces() override;

private:
  struct ActuatorConfig
  {
    std::string name;
    uint8_t     encoder_address;
    bool        has_external_encoder;
    int         mux_channel;
  };

  std::vector<Actuator>        actuators_;
  std::vector<ActuatorConfig>  actuator_configs_;
  Comms                        comms_;

  std::unordered_map<std::string, double> pos_;
  std::unordered_map<std::string, double> vel_;
  std::unordered_map<std::string, double> cmd_;
  std::unordered_map<std::string, double> prev_pos_;
};

} // namespace ros2_control_ers6
