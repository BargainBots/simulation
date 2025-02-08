// Copyright 2022 Open Source Robotics Foundation, Inc.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#include <memory>

#include <rclcpp/rclcpp.hpp>

#include <geometry_msgs/msg/twist_stamped.hpp>

using namespace std::chrono_literals;

int main(int argc, char * argv[])
{  
  if (argc > 3) {
    std::cerr << "Usage: " << argv[0] << " [linear_speed] [angular_speed]" << std::endl;
    return 1;
  }

  rclcpp::init(argc, argv);

  // Default values
  double linear_speed = 0.5;
  double angular_speed = 0.3;

  // Parse command line arguments if provided
  if (argc >= 2) {
    linear_speed = std::atof(argv[1]);
  }
  if (argc == 3) {
    angular_speed = std::atof(argv[2]);
  }


  std::shared_ptr<rclcpp::Node> node =
    std::make_shared<rclcpp::Node>("diff_drive_test_node");

  auto publisher = node->create_publisher<geometry_msgs::msg::TwistStamped>(
    "/diff_drive_base_controller/cmd_vel", 10);

  RCLCPP_INFO(node->get_logger(), "node created");

  geometry_msgs::msg::TwistStamped command;

  command.twist.linear.x = linear_speed;
  command.twist.linear.y = 0.0;
  command.twist.linear.z = 0.0;

  command.twist.angular.x = 0.0;
  command.twist.angular.y = 0.0;
  command.twist.angular.z = angular_speed;

  while (1) {
    command.header.stamp = node->now();
    publisher->publish(command);
    std::this_thread::sleep_for(50ms);
    rclcpp::spin_some(node);
  }
  rclcpp::shutdown();

  return 0;
}
