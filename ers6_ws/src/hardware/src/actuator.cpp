#include "hardware/actuator.hpp"

Actuator::Actuator(const std::string &name, int pca_channel,
                   bool uses_external_encoder, int mux_channel,
                   int min_us, int max_us)
  : name_(name), pca_channel_(pca_channel),
    has_external_encoder_(uses_external_encoder),
    mux_channel_(mux_channel), min_us_(min_us), max_us_(max_us) {}

const std::string & Actuator::get_name() const { return name_; }
int  Actuator::get_pca_channel() const { return pca_channel_; }
bool Actuator::uses_external_encoder() const { return has_external_encoder_; }
bool Actuator::uses_mux() const { return mux_channel_ >= 0; }
int  Actuator::get_mux_channel() const { return mux_channel_; }

void Actuator::set_position_rad(double p){ position_rad_ = p; }
void Actuator::set_command_rad(double c){ command_rad_ = c; }
double Actuator::get_command_rad() const { return command_rad_; }
double Actuator::get_position_rad() const { return position_rad_; }
