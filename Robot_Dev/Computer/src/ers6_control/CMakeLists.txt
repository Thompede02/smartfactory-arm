cmake_minimum_required(VERSION 3.8)
project(ers6_control)

find_package(ament_cmake REQUIRED)

# Install control-related assets (if present)
install(DIRECTORY urdf config
  DESTINATION share/${PROJECT_NAME}
  OPTIONAL
)

# Install executable Python scripts
install(PROGRAMS
  scripts/jog_from_sliders.py
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()
