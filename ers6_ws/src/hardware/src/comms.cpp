#include "hardware/comms.hpp"
#include <fcntl.h>
#include <unistd.h>
#include <sys/ioctl.h>
#include <linux/i2c-dev.h>
#include <cmath>

static constexpr uint8_t PCA_MODE1     = 0x00;
static constexpr uint8_t PCA_PRESCALE  = 0xFE;
static constexpr uint8_t PCA_LED0_ON_L = 0x06;

bool Comms::init(const std::string &device_path)
{
    i2c_fd_ = open(device_path.c_str(), O_RDWR);
    return i2c_fd_ >= 0;
}

bool Comms::set_addr_(uint8_t addr)
{
    return i2c_fd_ >= 0 && (ioctl(i2c_fd_, I2C_SLAVE, addr) >= 0);
}

bool Comms::write_byte_(uint8_t val) { return write(i2c_fd_, &val, 1) == 1; }

bool Comms::write_reg_(uint8_t reg, uint8_t val)
{
    uint8_t buf[2] = {reg, val};
    return write(i2c_fd_, buf, 2) == 2;
}

bool Comms::write_block_(uint8_t reg, const uint8_t *data, int n)
{
    uint8_t buf[1+4];
    if (n > 4) return false;
    buf[0] = reg;
    for (int i=0;i<n;i++) buf[1+i]=data[i];
    return write(i2c_fd_, buf, 1+n) == (1+n);
}

bool Comms::read_block_(uint8_t reg, uint8_t *data, int n)
{
    if (write(i2c_fd_, &reg, 1) != 1) return false;
    return read(i2c_fd_, data, n) == n;
}

/*** MUX ***/
bool Comms::select_mux_channel(uint8_t channel)
{
    if (channel > 7) return false;
    if (!set_addr_(0x70)) return false;
    uint8_t mask = (1u << channel);
    return write_byte_(mask);
}

/*** AS5600 ***/
bool Comms::read_encoder_deg(uint8_t as5600_addr, double &deg_out)
{
    if (!set_addr_(as5600_addr)) return false;
    uint8_t buf[2];
    // ANGLE 0x0E/0x0F
    if (!read_block_(0x0E, buf, 2)) return false;
    int raw12 = ((buf[0] << 8) | buf[1]) & 0x0FFF;
    deg_out = (raw12 * 360.0) / 4096.0;
    return true;
}

/*** PCA9685 ***/
bool Comms::pca_begin(uint8_t pca_addr, double hz)
{
    pca_addr_ = pca_addr; pca_hz_ = hz;
    if (!set_addr_(pca_addr_)) return false;

    // reset-ish
    if (!write_reg_(PCA_MODE1, 0x00)) return false;
    usleep(10000);

    int prescale = (int) std::round(25000000.0 / (4096.0 * hz) - 1.0);
    uint8_t oldmode;
    if (!read_block_(PCA_MODE1, &oldmode, 1)) return false;
    if (!write_reg_(PCA_MODE1, (oldmode & 0x7F) | 0x10)) return false; // sleep
    if (!write_reg_(PCA_PRESCALE, (uint8_t)prescale)) return false;
    if (!write_reg_(PCA_MODE1, oldmode)) return false;
    usleep(5000);
    return write_reg_(PCA_MODE1, oldmode | 0xA1); // restart + AI
}

bool Comms::pca_set_channel_ticks(int ch, int on_tick, int off_tick)
{
    if (!set_addr_(pca_addr_)) return false;
    uint8_t base = PCA_LED0_ON_L + 4*ch;
    uint8_t b[4] = {
        (uint8_t)(on_tick & 0xFF), (uint8_t)((on_tick >> 8) & 0x0F),
        (uint8_t)(off_tick & 0xFF), (uint8_t)((off_tick >> 8) & 0x0F)
    };
    return write_block_(base, b, 4);
}
