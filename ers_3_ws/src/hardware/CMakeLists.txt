cmake_minimum_required(VERSION 3.8)
project(hardware)

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(hardware_interface REQUIRED)
find_package(pluginlib REQUIRED)
find_package(rclcpp_lifecycle REQUIRED)

include_directories(include)

add_library(ros2_control_ers6 SHARED
  src/system.cpp
)

ament_target_dependencies(ros2_control_ers6
  rclcpp
  rclcpp_lifecycle
  hardware_interface
  pluginlib
)

set_target_properties(ros2_control_ers6 PROPERTIES
  C_STANDARD 99
  C_STANDARD_REQUIRED YES
)

pluginlib_export_plugin_description_file(hardware_interface hardware/system_plugin.xml)

install(TARGETS ros2_control_ers6
  EXPORT export_ros2_control_ers6
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION bin
)

install(DIRECTORY include/
  DESTINATION include/
)

install(FILES hardware/system_plugin.xml
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
