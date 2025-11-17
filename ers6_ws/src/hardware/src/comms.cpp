#include "hardware/comms.hpp"
#include "hardware/pca9685_min.h"

#include <fcntl.h>
#include <unistd.h>
#include <sys/ioctl.h>
#include <linux/i2c-dev.h>
#include <iostream>

Comms::~Comms() {
  if (fd_ >= 0) ::close(fd_);
}

bool Comms::init(const std::string& dev) {
  fd_ = ::open(dev.c_str(), O_RDWR);
  if (fd_ < 0) {
    std::cerr << "[hw] open " << dev << " failed\n";
    return false;
  }

  // Init PCA + set 50Hz + go neutral
  if (pca_init(fd_, pca_addr_) < 0) {
    std::cerr << "[hw] pca_init failed\n";
    return false;
  }
  if (pca_set_frequency(50.0) < 0) {
    std::cerr << "[hw] pca_set_frequency failed\n";
    return false;
  }

  // Neutral (0 rad) on startup
  return neutral_all();
}

bool Comms::neutral_all() {
  double zeros[6] = {0,0,0,0,0,0};
  return Update_Servo_Angles(zeros) == 0;
}

bool Comms::write_pca9685_rad(const std::array<double,6>& r) {
  return Update_Servo_Angles(r.data()) == 0;
}

// ---------- Optional MUX + AS5600 (no-op until wired) ----------
bool Comms::select_mux_channel(uint8_t channel) {
  if (fd_ < 0 || channel > 7) return false;
  if (ioctl(fd_, I2C_SLAVE, mux_addr_) < 0) return false;
  uint8_t d = static_cast<uint8_t>(1u << channel);
  return write(fd_, &d, 1) == 1;
}

bool Comms::read_encoder(uint8_t encoder_addr, double& deg) {
  if (fd_ < 0) return false;
  if (ioctl(fd_, I2C_SLAVE, encoder_addr) < 0) return false;

  uint8_t reg = 0x0C; // RAW_ANGLE
  if (write(fd_, &reg, 1) != 1) return false;

  uint8_t b[2]{};
  if (read(fd_, b, 2) != 2) return false;

  uint16_t raw = ((uint16_t)b[0] << 8 | b[1]) & 0x0FFF; // 12-bit
  deg = raw * (360.0/4096.0);
  return true;
}
