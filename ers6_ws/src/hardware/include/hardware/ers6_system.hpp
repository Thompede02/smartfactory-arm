#pragma once

#include <string>
#include <unordered_map>
#include <vector>

#include "hardware_interface/system_interface.hpp"
#include "hardware_interface/types/hardware_interface_return_values.hpp"
#include "hardware_interface/types/hardware_interface_type_values.hpp"
#include "hardware_interface/handle.hpp"
#include "hardware_interface/hardware_info.hpp"
#include "rclcpp_lifecycle/lifecycle_node.hpp"

#include "hardware/comms.hpp"
#include "hardware/actuator.hpp"

using hardware_interface::return_type;

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

  return_type read(const rclcpp::Time & time, const rclcpp::Duration & period) override;
  return_type write(const rclcpp::Time & time, const rclcpp::Duration & period) override;

  std::vector<hardware_interface::StateInterface> export_state_interfaces() override;
  std::vector<hardware_interface::CommandInterface> export_command_interfaces() override;

private:
  struct ActuatorConfig
  {
    std::string name;
    int pca_channel;
    bool has_external_encoder;
    int mux_channel;
    int min_us;
    int max_us;

    ActuatorConfig(const std::string &n, int ch, bool ext, int muxc, int mi, int ma)
      : name(n), pca_channel(ch), has_external_encoder(ext), mux_channel(muxc), min_us(mi), max_us(ma) {}
  };

  std::vector<Actuator> actuators_;
  std::vector<ActuatorConfig> actuator_configs_;

  Comms comms_;

  std::unordered_map<std::string, double> pos_rad_;
  std::unordered_map<std::string, double> vel_rad_;
  std::unordered_map<std::string, double> cmd_rad_;
  std::unordered_map<std::string, double> prev_pos_rad_;

  // helpers
  static inline double rad2deg_(double r){ return r * 180.0 / M_PI; }
  static inline double clamp_(double v,double lo,double hi){ return v<lo?lo:(v>hi?hi:v); }
};

}  // namespace ros2_control_ers6
