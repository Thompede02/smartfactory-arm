#pragma once
#include <stdint.h>

#ifdef __cplusplus
extern "C"
{
#endif

    int pca_init(int I2C_File_Descriptor, uint8_t Servo_Address);
    int pca_set_frequency(double Hertz);
    int Update_Servo_Angles(const double *Angles_To_Rad); // 6 elements, radians

#ifdef __cplusplus
}
#endif
