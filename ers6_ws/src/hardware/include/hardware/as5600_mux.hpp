#pragma once
#include <cstdint>

class AS5600Mux
{
public:
  AS5600Mux() = default;
  void attach(int fd, uint8_t mux_addr = 0x70) { fd_ = fd; mux_ = mux_addr; }

  bool select(uint8_t channel);
  bool read_deg(uint8_t encoder_addr, double &deg);

private:
  int     fd_  = -1;
  uint8_t mux_ = 0x70;
};
