cmake_minimum_required(VERSION 3.8)
project(hardware)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(hardware_interface REQUIRED)
find_package(pluginlib REQUIRED)

# i2c headers/libs
find_path(I2C_INCLUDE_DIRS linux/i2c-dev.h)
find_library(I2C_LIB i2c)
if(NOT I2C_INCLUDE_DIRS OR NOT I2C_LIB)
  message(FATAL_ERROR "libi2c-dev missing. Install: sudo apt-get install -y libi2c-dev")
endif()

include_directories(
  include
  ${I2C_INCLUDE_DIRS}
)

add_library(ros2_control_ers6 SHARED
  src/actuator.cpp
  src/comms.cpp
  src/ers6_system.cpp
)

target_compile_features(ros2_control_ers6 PUBLIC cxx_std_17)
ament_target_dependencies(ros2_control_ers6 rclcpp hardware_interface pluginlib)
target_link_libraries(ros2_control_ers6 ${I2C_LIB})

pluginlib_export_plugin_description_file(hardware_interface hardware/ers6_system_plugin.xml)

install(TARGETS ros2_control_ers6
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION bin
)

install(DIRECTORY include/ DESTINATION include)
install(DIRECTORY hardware/ DESTINATION share/${PROJECT_NAME}/hardware)
install(DIRECTORY urdf/     DESTINATION share/${PROJECT_NAME}/urdf)

ament_package()
