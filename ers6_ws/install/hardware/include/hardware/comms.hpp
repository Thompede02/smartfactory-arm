#pragma once
#include <cstdint>
#include <string>

class Comms
{
public:
    bool init(const std::string &device_path);

    // encoders (via currently selected mux)
    bool read_encoder_deg(uint8_t as5600_addr, double &deg_out);

    // mux
    bool select_mux_channel(uint8_t channel);

    // pca9685
    bool pca_begin(uint8_t pca_addr, double hz);
    bool pca_set_channel_ticks(int ch, int on_tick, int off_tick);

private:
    int i2c_fd_ = -1;
    uint8_t pca_addr_{0x40};
    double  pca_hz_{50.0};

    bool set_addr_(uint8_t addr);
    bool write_byte_(uint8_t val);
    bool write_reg_(uint8_t reg, uint8_t val);
    bool write_block_(uint8_t reg, const uint8_t *data, int n);
    bool read_block_(uint8_t reg, uint8_t *data, int n);
};
