#include "hardware/ers6_system.hpp"
#include <rclcpp/logging.hpp>
#include <chrono>
#include <thread>
#include <map>
#include <array>
#include <cmath>

namespace ros2_control_ers6
{

CallbackReturn RobotSystemHardware::on_init(const hardware_interface::HardwareInfo & info)
{
  if (hardware_interface::SystemInterface::on_init(info) != CallbackReturn::SUCCESS)
    return CallbackReturn::ERROR;

  // Encoders planned for last 3 joints via TCA later; first 3 open-loop for now.
  actuator_configs_ = {
    {"base_link_to_a5", 0x00, false, -1},
    {"a5_to_a4",        0x00, false, -1},
    {"a4_to_a3",        0x00, false, -1},
    {"a3_to_a2",        0x36, false,   0},
    {"a2_to_a1",        0x36, false,   1},
    {"a1_to_a0",        0x36, false,   2}
  };

  actuators_.reserve(actuator_configs_.size());
  for (const auto & cfg : actuator_configs_)
  {
    actuators_.emplace_back(cfg.name, cfg.encoder_address, cfg.mux_channel, cfg.has_external_encoder);

    pos_[cfg.name] = 0.0;
    vel_[cfg.name] = 0.0;
    prev_pos_[cfg.name] = 0.0;
    cmd_[cfg.name] = 0.0;
  }

  if (comms_.init("/dev/i2c-1")) {
    RCLCPP_INFO(rclcpp::get_logger("hardware"), "I2C initialized on /dev/i2c-1");
  } else {
    RCLCPP_ERROR(rclcpp::get_logger("hardware"), "Failed to initialize I2C on /dev/i2c-1");
    return CallbackReturn::ERROR;
  }

  return CallbackReturn::SUCCESS;
}

CallbackReturn RobotSystemHardware::on_configure(const rclcpp_lifecycle::State &)
{
  return CallbackReturn::SUCCESS;
}

CallbackReturn RobotSystemHardware::on_activate(const rclcpp_lifecycle::State &)
{
  // Mechanical neutral at startup: 0 rad => 1.5 ms pulse
  constexpr double HOME = 0.0;

  for (auto & a : actuators_)
  {
    const std::string & name = a.get_name();
    cmd_[name] = HOME;
    a.set_command(HOME);

    // Prime state to avoid a velocity spike on first read
    pos_[name] = HOME;
    prev_pos_[name] = HOME;
  }

  RCLCPP_INFO(rclcpp::get_logger("hardware"),
              "Activated: set initial HOME = 0 rad (mechanical neutral) for all joints");

  return CallbackReturn::SUCCESS;
}

CallbackReturn RobotSystemHardware::on_deactivate(const rclcpp_lifecycle::State &)
{
  return CallbackReturn::SUCCESS;
}

hardware_interface::return_type RobotSystemHardware::read(const rclcpp::Time &, const rclcpp::Duration & period)
{
  for (auto & actuator : actuators_)
  {
    if (actuator.uses_external_encoder())
    {
      if (actuator.uses_mux()) {
        if (!comms_.select_mux_channel(actuator.get_mux_channel())) {
          RCLCPP_ERROR(rclcpp::get_logger("hardware"),
                       "Failed to select mux channel %d for %s",
                       actuator.get_mux_channel(), actuator.get_name().c_str());
          continue;
        }
      }

      double position_deg = 0.0;
      if (actuator.get_encoder_address() != 0x00 &&
          comms_.read_encoder(actuator.get_encoder_address(), position_deg))
      {
        double position = position_deg * M_PI / 180.0;
        actuator.set_position(position);
        pos_[actuator.get_name()] = position;

        const double dt = period.seconds();
        const double prev = prev_pos_[actuator.get_name()];
        vel_[actuator.get_name()] = (position - prev) / dt;
        prev_pos_[actuator.get_name()] = position;
      }
      else
      {
        // Encoder not present yet; keep previous
      }
    }
    else
    {
      // Open-loop joints: pos follows command
      const double position = actuator.get_command();
      actuator.set_position(position);
      pos_[actuator.get_name()] = position;

      const double dt = period.seconds();
      const double prev = prev_pos_[actuator.get_name()];
      vel_[actuator.get_name()] = (position - prev) / dt;
      prev_pos_[actuator.get_name()] = position;
    }
  }

  return hardware_interface::return_type::OK;
}

hardware_interface::return_type RobotSystemHardware::write(const rclcpp::Time &, const rclcpp::Duration &)
{
  std::array<double, 6> targets{};
  size_t i = 0;
  for (auto & actuator : actuators_)
  {
    const double c = cmd_[actuator.get_name()];
    actuator.set_command(c);
    if (i < targets.size())
      targets[i] = c;
    ++i;
  }

  if (!comms_.write_pca9685_rad(targets)) {
    RCLCPP_ERROR(rclcpp::get_logger("hardware"), "PCA9685 write failed");
  }

  return hardware_interface::return_type::OK;
}

std::vector<hardware_interface::StateInterface> RobotSystemHardware::export_state_interfaces()
{
  std::vector<hardware_interface::StateInterface> state_interfaces;
  for (const auto & cfg : actuator_configs_)
  {
    state_interfaces.emplace_back(cfg.name, hardware_interface::HW_IF_POSITION, &pos_[cfg.name]);
    state_interfaces.emplace_back(cfg.name, hardware_interface::HW_IF_VELOCITY, &vel_[cfg.name]);
  }
  return state_interfaces;
}

std::vector<hardware_interface::CommandInterface> RobotSystemHardware::export_command_interfaces()
{
  std::vector<hardware_interface::CommandInterface> command_interfaces;
  for (const auto & cfg : actuator_configs_)
  {
    command_interfaces.emplace_back(cfg.name, hardware_interface::HW_IF_POSITION, &cmd_[cfg.name]);
  }
  return command_interfaces;
}

} // namespace ros2_control_ers6

#include "pluginlib/class_list_macros.hpp"
PLUGINLIB_EXPORT_CLASS(
  ros2_control_ers6::RobotSystemHardware, hardware_interface::SystemInterface)
