cmake_minimum_required(VERSION 3.8)
project(ers6_description)

find_package(ament_cmake REQUIRED)

install(DIRECTORY urdf meshes rviz
  DESTINATION share/${PROJECT_NAME}
)

install(DIRECTORY launch
  DESTINATION share/${PROJECT_NAME}
  OPTIONAL
)

ament_package()
