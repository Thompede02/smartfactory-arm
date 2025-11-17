#include <stdint.h>
#include <unistd.h>
#include <sys/ioctl.h>
#include <linux/i2c-dev.h>
#include <math.h>
#include "hardware/pca9685_min.h"

// PCA9685 registers
static const uint8_t MODE_1 = 0x00;
static const uint8_t MODE_2 = 0x01;
static const uint8_t PRE_SCALE = 0xFE;
static const uint8_t LED0_ON_L = 0x06;
static const uint8_t ALL_LED_OFF_H = 0xFD;

// GLOBALS
static int I2C_File_Descriptor = -1;
static uint8_t Servo_Address = 0x40;
static double Servo_Frequency = 50.0;

static int Select_Slave_Address(uint8_t Address)
{
    return ioctl(I2C_File_Descriptor, I2C_SLAVE, Address);
}

// ONE BYTE REGISTER
static int One_Byte_Register(uint8_t Register_Address, uint8_t Data)
{
    uint8_t Buffer[2] = {Register_Address, Data};
    return (write(I2C_File_Descriptor, Buffer, 2) == 2) ? 0 : -1;
}

// FOUR BYTES (channel block)
static int Four_Byte_Register(int Channel, uint16_t ON, uint16_t OFF)
{
    const uint8_t OFFS_ON_L = 0;
    const uint8_t OFFS_ON_H = 1;
    const uint8_t OFFS_OFF_L = 2;
    const uint8_t OFFS_OFF_H = 3;
    const uint8_t Start = LED0_ON_L + (uint8_t)(4 * Channel);

    if (One_Byte_Register(Start + OFFS_ON_L, ON & 0xFF) < 0)
        return -1;
    if (One_Byte_Register(Start + OFFS_ON_H, (ON >> 8) & 0x0F) < 0)
        return -1;
    if (One_Byte_Register(Start + OFFS_OFF_L, OFF & 0xFF) < 0)
        return -1;
    if (One_Byte_Register(Start + OFFS_OFF_H, (OFF >> 8) & 0x0F) < 0)
        return -1;

    return 0;
}

int pca_init(int I2C_FD, uint8_t Servo_Addr)
{
    I2C_File_Descriptor = I2C_FD;
    Servo_Address = Servo_Addr;

    if (Select_Slave_Address(Servo_Address) < 0)
        return -1;

    // Wake
    if (One_Byte_Register(MODE_1, 0x00) < 0)
        return -1;
    usleep(2000);

    // Totem-pole outputs
    if (One_Byte_Register(MODE_2, 0x04) < 0)
        return -1;

    // Safe full-off all channels
    if (One_Byte_Register(ALL_LED_OFF_H, 0x10) < 0)
        return -1;

    return 0;
}

int pca_set_frequency(double Hertz)
{
    if (Hertz < 10.0)
        Hertz = 10.0;
    if (Hertz > 1000.0)
        Hertz = 1000.0;

    if (Select_Slave_Address(Servo_Address) < 0)
        return -1;

    double Prescale = floor(25000000.0 / (4096.0 * Hertz) + 0.5) - 1.0;
    if (Prescale < 3.0)
        Prescale = 3.0;
    if (Prescale > 255.0)
        Prescale = 255.0;

    if (One_Byte_Register(MODE_1, 0x10) < 0)
        return -1; // sleep
    if (One_Byte_Register(PRE_SCALE, (uint8_t)Prescale) < 0)
        return -1;
    if (One_Byte_Register(MODE_1, 0x00) < 0)
        return -1; // wake
    usleep(3500);
    if (One_Byte_Register(MODE_1, 0x20) < 0)
        return -1; // AI on

    Servo_Frequency = Hertz;
    return 0;
}

int Update_Servo_Angles(const double *Angles_To_Rad)
{
    if (Select_Slave_Address(Servo_Address) < 0)
        return -1;

    for (int Ch = 0; Ch < 6; ++Ch)
    {
        double x = Angles_To_Rad[Ch];
        if (x < -M_PI / 2)
            x = -M_PI / 2;
        if (x > M_PI / 2)
            x = M_PI / 2;

        double t = (x + M_PI / 2) / M_PI;      // 0..1
        int us = (int)(1000 + t * 1000 + 0.5); // 1000..2000 µs

        // µs -> 12-bit counts for current frequency
        double counts_f = (us * Servo_Frequency * 4096.0) / 1e6;
        if (counts_f < 0)
            counts_f = 0;
        if (counts_f > 4095)
            counts_f = 4095;

        uint16_t OFF = (uint16_t)(counts_f + 0.5);
        if (Four_Byte_Register(Ch, 0, OFF) < 0)
            return -1;
    }
    return 0;
}
