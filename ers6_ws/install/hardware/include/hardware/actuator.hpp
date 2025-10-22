#pragma once
#include <string>

class Actuator
{
public:
    // PCA9685 channel + optional AS5600 on mux channel
    Actuator(const std::string &name, int pca_channel,
             bool uses_external_encoder, int mux_channel,
             int min_us, int max_us);

    const std::string & get_name() const;
    int  get_pca_channel() const;
    bool uses_external_encoder() const;
    int  get_mux_channel() const;
    bool uses_mux() const;

    void   set_position_rad(double pos_rad);
    void   set_command_rad(double cmd_rad);
    double get_command_rad() const;
    double get_position_rad() const;

    int min_us() const { return min_us_; }
    int max_us() const { return max_us_; }

private:
    std::string name_;
    int pca_channel_{0};
    bool has_external_encoder_{false};
    int mux_channel_{-1};
    int min_us_{500};
    int max_us_{2400};

    double position_rad_{0.0};
    double command_rad_{0.0};
};

