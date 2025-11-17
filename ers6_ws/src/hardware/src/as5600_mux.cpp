#include "hardware/as5600_mux.hpp"
#include <linux/i2c-dev.h>
#include <sys/ioctl.h>
#include <unistd.h>

static inline bool set_addr(int fd, uint8_t a){ return ioctl(fd, I2C_SLAVE, a) >= 0; }

bool AS5600Mux::select(uint8_t ch)
{
  if (fd_ < 0 || ch > 7) return false;
  if (!set_addr(fd_, mux_)) return false;
  uint8_t d = static_cast<uint8_t>(1u << ch);
  return write(fd_, &d, 1) == 1;
}

bool AS5600Mux::read_deg(uint8_t enc_addr, double &deg)
{
  if (fd_ < 0) return false;
  if (!set_addr(fd_, enc_addr)) return false;

  uint8_t reg = 0x0C; // RAW_ANGLE (MSB at 0x0C, LSB at 0x0D)
  if (write(fd_, &reg, 1) != 1) return false;

  uint8_t b[2]{};
  if (read(fd_, b, 2) != 2) return false;

  uint16_t raw = ((uint16_t)b[0] << 8 | b[1]) & 0x0FFF; // 12-bit
  deg = raw * (360.0 / 4096.0);
  return true;
}
