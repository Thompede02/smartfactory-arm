#pragma once
#include <string>
#include <array>
#include <cstdint>

class Comms {
public:
  ~Comms();
  bool init(const std::string& dev = "/dev/i2c-1");

  // PCA9685
  bool neutral_all();                                   // send 0 rad to all 6
  bool write_pca9685_rad(const std::array<double,6>& r);// send 6 rad

  // MUX + AS5600 (optional; safe no-op until you wire them)
  bool select_mux_channel(uint8_t channel);
  bool read_encoder(uint8_t encoder_addr, double& deg);

private:
  int fd_ = -1;           // /dev/i2c-1
  uint8_t pca_addr_ = 0x40;
  uint8_t mux_addr_ = 0x70;
};
