#include "hardware/system.hpp"

#include <algorithm>

#include "hardware_interface/handle.hpp"
#include "hardware_interface/types/hardware_interface_type_values.hpp"
#include "pluginlib/class_list_macros.hpp"

namespace ros2_control_ers6
{

  using hardware_interface::CallbackReturn;
  using hardware_interface::return_type;

  CallbackReturn RobotSystemHardware::on_init(
      const hardware_interface::HardwareInfo &info)
  {
    if (hardware_interface::SystemInterface::on_init(info) != CallbackReturn::SUCCESS)
    {
      RCLCPP_ERROR(rclcpp::get_logger("hardware"), "Initilaization Failed");
      return CallbackReturn::ERROR;
    }

    // Collect joint names from hardware
    joint_names_.clear();
    for (const auto &joint : info_.joints)
    {
      joint_names_.push_back(joint.name);
    }

    std::size_t n = joint_names_.size();
    pos_.assign(n, 0.0);
    vel_.assign(n, 0.0);
    cmd_.assign(n, 0.0);

    // Encoder state arrays (same size as joints)
    enc_pos_.assign(n, 0.0);
    enc_ok_.assign(n, false);

    // Build name → index map (for fast lookup in encoder_callback)

    name_to_index_.clear();
    for (std::size_t i = 0; i < joint_names_.size(); ++i)
    {
      name_to_index_[joint_names_[i]] = i;
    }

    // Internal ROS node
    node_ = rclcpp::Node::make_shared("ers6_hardware_node");

    // Publisher to servo Python node
    servo_pub_ = node_->create_publisher<std_msgs::msg::Float64MultiArray>(
        "/servo_target_rad", 10);

    // Subscriber from encoder Python node
    encoder_sub_ = node_->create_subscription<sensor_msgs::msg::JointState>(
        "/encoder_joint_states",
        10,
        std::bind(&RobotSystemHardware::encoder_callback, this, std::placeholders::_1));

    // Executor to let us process encoder callbacks inside read()
    executor_ = std::make_shared<rclcpp::executors::SingleThreadedExecutor>();
    executor_->add_node(node_);

    RCLCPP_INFO(
        rclcpp::get_logger("hardware"),
        "RobotSystemHardware initialized with %zu joints.", joint_names_.size());

    return CallbackReturn::SUCCESS;
  }

  void RobotSystemHardware::encoder_callback(
      const sensor_msgs::msg::JointState::SharedPtr msg)
  {
    // Find matching joint index per joint
    for (std::size_t i = 0; i < msg->name.size() && i < msg->position.size(); ++i)
    {
      auto it = name_to_index_.find(msg->name[i]);
      if (it == name_to_index_.end())
      {
        // Joint name not found (Continue)
        continue;
      }

      std::size_t idx = it->second;
      enc_pos_[idx] = msg->position[i];
      enc_ok_[idx] = true;
    }
  }

  CallbackReturn RobotSystemHardware::on_configure(
      const rclcpp_lifecycle::State &)
  {
    std::fill(pos_.begin(), pos_.end(), 0.0);
    std::fill(vel_.begin(), vel_.end(), 0.0);
    std::fill(cmd_.begin(), cmd_.end(), 0.0);
    std::fill(enc_pos_.begin(), enc_pos_.end(), 0.0);
    std::fill(enc_ok_.begin(), enc_ok_.end(), false);

    return CallbackReturn::SUCCESS;
  }

  CallbackReturn RobotSystemHardware::on_activate(
      const rclcpp_lifecycle::State &state)
  {
    (void)state;
    return on_configure(state);
  }

  CallbackReturn RobotSystemHardware::on_deactivate(
      const rclcpp_lifecycle::State &)
  {
    return CallbackReturn::SUCCESS;
  }

  return_type RobotSystemHardware::read(
      const rclcpp::Time &,
      const rclcpp::Duration &period)
  {
    // Processing pending encoder callbacks
    if (executor_)
    {
      executor_->spin_some();
    }

    double dt = period.seconds();
    std::size_t n = joint_names_.size();

    for (std::size_t i = 0; i < n; ++i)
    {
      double prev = pos_[i];

      // If any encoder data use it other wise closed loop.
      if (enc_ok_[i])
      {
        pos_[i] = enc_pos_[i];
      }
      else
      {
        pos_[i] = cmd_[i];
      }

      vel_[i] = (dt > 0.0) ? (pos_[i] - prev) / dt : 0.0;
    }

    return return_type::OK;
  }

  return_type RobotSystemHardware::write(
      const rclcpp::Time &,
      const rclcpp::Duration &)
  {
    if (!servo_pub_)
    {
      RCLCPP_ERROR(rclcpp::get_logger("hardware"), "servo_pub_ not set");
      return return_type::ERROR;
    }

    std_msgs::msg::Float64MultiArray msg;
    msg.data = cmd_;
    servo_pub_->publish(msg);
    return return_type::OK;
  }

  std::vector<hardware_interface::StateInterface>
  RobotSystemHardware::export_state_interfaces()
  {
    std::vector<hardware_interface::StateInterface> v;
    v.reserve(joint_names_.size() * 2);

    for (std::size_t i = 0; i < joint_names_.size(); ++i)
    {
      v.emplace_back(joint_names_[i], hardware_interface::HW_IF_POSITION, &pos_[i]);
      v.emplace_back(joint_names_[i], hardware_interface::HW_IF_VELOCITY, &vel_[i]);
    }
    return v;
  }

  std::vector<hardware_interface::CommandInterface>
  RobotSystemHardware::export_command_interfaces()
  {
    std::vector<hardware_interface::CommandInterface> v;
    v.reserve(joint_names_.size());

    for (std::size_t i = 0; i < joint_names_.size(); ++i)
    {
      v.emplace_back(joint_names_[i], hardware_interface::HW_IF_POSITION, &cmd_[i]);
    }
    return v;
  }

} // namespace ros2_control_ers6

PLUGINLIB_EXPORT_CLASS(
    ros2_control_ers6::RobotSystemHardware,
    hardware_interface::SystemInterface)
