#pragma once
#include <string>
#include <cstdint>

class Actuator
{
public:
  Actuator(const std::string &name,
           uint8_t encoder_addr,
           int mux_channel,
           bool uses_external_encoder);

  const std::string & get_name() const { return name_; }
  uint8_t get_encoder_address() const  { return encoder_addr_; }
  int get_mux_channel() const          { return mux_channel_; }
  bool uses_external_encoder() const   { return has_external_encoder_; }
  bool uses_mux() const                { return mux_channel_ >= 0; }

  void   set_position(double pos) { position_ = pos; }
  void   set_command(double cmd)  { command_  = cmd; }
  double get_position() const     { return position_; }
  double get_command() const      { return command_; }

private:
  std::string name_;
  uint8_t     encoder_addr_;
  int         mux_channel_;
  bool        has_external_encoder_;

  double position_ = 0.0;
  double command_  = 0.0;
};
