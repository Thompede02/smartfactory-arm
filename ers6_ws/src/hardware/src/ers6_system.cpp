#include "hardware/ers6_system.hpp"
#include <rclcpp/logging.hpp>
#include <cmath>

namespace ros2_control_ers6
{
    // A steady clock for RCLCPP_*_THROTTLE macros (we're not a Node)
    static rclcpp::Clock g_steady_clock(RCL_STEADY_TIME);

    using CB = rclcpp_lifecycle::node_interfaces::LifecycleNodeInterface::CallbackReturn;

    static int us_to_ticks(double us, double hz)
    {
        const double period_us = 1e6 / hz; // e.g. 20000 at 50Hz
        int t = (int)std::round((us / period_us) * 4096.0);
        if (t < 0)
            t = 0;
        if (t > 4095)
            t = 4095;
        return t;
    }

    CallbackReturn RobotSystemHardware::on_init(const hardware_interface::HardwareInfo &info)
    {
        if (hardware_interface::SystemInterface::on_init(info) != CallbackReturn::SUCCESS)
            return CallbackReturn::ERROR;

        // Keep friend naming; 6 joints. Add 'gripper' if you need a 7th.
        actuator_configs_ = {
            // name,             pca_ch, enc?, mux_ch, min_us, max_us
            {"base_link_to_a5", 0, true, 0, 500, 2400}, // encoder on mux CH0
            {"a5_to_a4", 1, true, 1, 500, 2400},        // encoder on mux CH1
            {"a4_to_a3", 2, false, -1, 500, 2400},
            {"a3_to_a2", 3, false, -1, 500, 2400},
            {"a2_to_a1", 4, false, -1, 500, 2400},
            {"a1_to_a0", 5, false, -1, 500, 2400}
            // {"gripper",         6,     false, -1,     900,   2100}
        };

        actuators_.clear();
        for (const auto &cfg : actuator_configs_)
        {
            actuators_.emplace_back(cfg.name, cfg.pca_channel, cfg.has_external_encoder,
                                    cfg.mux_channel, cfg.min_us, cfg.max_us);
            pos_rad_[cfg.name] = 0.0;
            vel_rad_[cfg.name] = 0.0;
            prev_pos_rad_[cfg.name] = 0.0;
            cmd_rad_[cfg.name] = 0.0;
        }

        if (comms_.init("/dev/i2c-1"))
        {
            RCLCPP_INFO(rclcpp::get_logger("hardware"), "I2C ok on /dev/i2c-1");
        }
        else
        {
            RCLCPP_ERROR(rclcpp::get_logger("hardware"), "I2C open failed");
            return CallbackReturn::ERROR;
        }

        // init PCA9685 0x40 @ 50Hz
        if (!comms_.pca_begin(0x40, 50.0))
        {
            RCLCPP_ERROR(rclcpp::get_logger("hardware"), "PCA9685 init failed (0x40)");
            return CallbackReturn::ERROR;
        }
        RCLCPP_INFO(rclcpp::get_logger("hardware"), "PCA9685 ready @0x40; TCA9548A @0x70");

        return CallbackReturn::SUCCESS;
    }

    CallbackReturn RobotSystemHardware::on_configure(const rclcpp_lifecycle::State &) { return CallbackReturn::SUCCESS; }
    CallbackReturn RobotSystemHardware::on_activate(const rclcpp_lifecycle::State &) { return CallbackReturn::SUCCESS; }
    CallbackReturn RobotSystemHardware::on_deactivate(const rclcpp_lifecycle::State &) { return CallbackReturn::SUCCESS; }

    return_type RobotSystemHardware::read(const rclcpp::Time &, const rclcpp::Duration &period)
    {
        // Encoders: deg -> rad; others: open-loop (state = last command)
        for (auto &a : actuators_)
        {
            if (a.uses_external_encoder())
            {
                if (a.uses_mux())
                {
                    if (!comms_.select_mux_channel((uint8_t)a.get_mux_channel()))
                    {

                        // RCLCPP_WARN_THROTTLE(rclcpp::get_logger("hardware"), *rclcpp::get_clock().get(), 2000,
                        //"MUX select failed ch=%d (%s)", a.get_mux_channel(), a.get_name().c_str());
                        RCLCPP_WARN_THROTTLE(
                            rclcpp::get_logger("hardware"), g_steady_clock, 2000,
                            "MUX select failed ch=%d (%s)", a.get_mux_channel(), a.get_name().c_str());

                        continue;
                    }
                }
                double deg = 0.0;
                if (comms_.read_encoder_deg(0x36, deg))
                {
                    // NOTE: add zero/invert later if needed
                    double rad = deg * M_PI / 180.0;
                    a.set_position_rad(rad);
                    pos_rad_[a.get_name()] = rad;
                }
                else
                {
                    // RCLCPP_WARN_THROTTLE(rclcpp::get_logger("hardware"), *rclcpp::get_clock().get(), 2000,
                    //"AS5600 read failed (%s)", a.get_name().c_str());
                    RCLCPP_WARN_THROTTLE(
                        rclcpp::get_logger("hardware"), g_steady_clock, 2000,
                        "AS5600 read failed (%s)", a.get_name().c_str());
                }
            }
            else
            {
                pos_rad_[a.get_name()] = a.get_command_rad();
            }
        }

        const double dt = period.seconds();
        if (dt > 1e-6)
        {
            for (auto &a : actuators_)
            {
                double p = pos_rad_[a.get_name()];
                double prev = prev_pos_rad_[a.get_name()];
                vel_rad_[a.get_name()] = (p - prev) / dt;
                prev_pos_rad_[a.get_name()] = p;
            }
        }
        return return_type::OK;
    }

    return_type RobotSystemHardware::write(const rclcpp::Time &, const rclcpp::Duration &)
    {
        // cmd (rad) -> us -> ticks -> PCA
        for (auto &a : actuators_)
        {
            const std::string &n = a.get_name();
            double deg = rad2deg_(cmd_rad_[n]);
            deg = clamp_(deg, 0.0, 180.0); // universal clamp for hobby servos
            double us = a.min_us() + (deg / 180.0) * (a.max_us() - a.min_us());
            int ticks = us_to_ticks(us, 50.0);
            if (!comms_.pca_set_channel_ticks(a.get_pca_channel(), 0, ticks))
            {
                // RCLCPP_WARN_THROTTLE(rclcpp::get_logger("hardware"), *rclcpp::get_clock().get(), 2000,
                //"PCA write failed ch=%d (%s)", a.get_pca_channel(), n.c_str());

                RCLCPP_WARN_THROTTLE(
                    rclcpp::get_logger("hardware"), g_steady_clock, 2000,
                    "PCA write failed ch=%d (%s)", a.get_pca_channel(), n.c_str());
            }
            a.set_command_rad(cmd_rad_[n]);
        }
        return return_type::OK;
    }

    std::vector<hardware_interface::StateInterface> RobotSystemHardware::export_state_interfaces()
    {
        std::vector<hardware_interface::StateInterface> state_interfaces;
        for (const auto &cfg : actuator_configs_)
        {
            state_interfaces.emplace_back(cfg.name, hardware_interface::HW_IF_POSITION, &pos_rad_[cfg.name]);
            state_interfaces.emplace_back(cfg.name, hardware_interface::HW_IF_VELOCITY, &vel_rad_[cfg.name]);
        }
        return state_interfaces;
    }

    std::vector<hardware_interface::CommandInterface> RobotSystemHardware::export_command_interfaces()
    {
        std::vector<hardware_interface::CommandInterface> command_interfaces;
        for (const auto &cfg : actuator_configs_)
        {
            command_interfaces.emplace_back(cfg.name, hardware_interface::HW_IF_POSITION, &cmd_rad_[cfg.name]);
        }
        return command_interfaces;
    }

} // namespace ros2_control_ers6

#include "pluginlib/class_list_macros.hpp"
PLUGINLIB_EXPORT_CLASS(
    ros2_control_ers6::RobotSystemHardware, hardware_interface::SystemInterface)
