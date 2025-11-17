#include "hardware/actuator.hpp"

Actuator::Actuator(const std::string &name,
                   uint8_t encoder_addr,
                   int mux_channel,
                   bool uses_external_encoder)
: name_(name),
  encoder_addr_(encoder_addr),
  mux_channel_(mux_channel),
  has_external_encoder_(uses_external_encoder)
{}
