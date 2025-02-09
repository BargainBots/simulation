# Copyright 2022 Open Source Robotics Foundation, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction
from launch.actions import RegisterEventHandler
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, FindExecutable, LaunchConfiguration, PathJoinSubstitution

from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    # Launch Arguments
    use_sim_time = LaunchConfiguration('use_sim_time', default=True)
    launch_description = []

    def spawn_entity(name, x, y, z):
        # Get URDF or SDF via xacro
        robot_description_content = Command(
            [
                PathJoinSubstitution([FindExecutable(name='xacro')]),
                ' ',
                PathJoinSubstitution([
                    FindPackageShare('bargain_bots_demos'),
                    "urdf",
                    f'test_diff_drive.xacro.urdf'
                ]),
                ' ',
                f'namespace:={name}',
            ]
        )
        robot_description = {'robot_description': robot_description_content}
        node_robot_state_publisher = Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            output='screen',
            namespace=name,
            parameters=[robot_description]
        )

        robot_controllers = PathJoinSubstitution(
            [
                FindPackageShare('bargain_bots_demos'),
                'config',
                'diff_drive_controller.yaml',
            ]
        )

        gz_spawn_entity = Node(
            package='ros_gz_sim',
            executable='create',
            output='screen',
            namespace=name,
            arguments=['-topic', 'robot_description', '-name',
                       'diff_drive', '-allow_renaming', 'true',
                       '-x', x, '-y', y, '-z', z
                       ],
        )
        joint_state_broadcaster_spawner = Node(
            package='controller_manager',
            executable='spawner',
            arguments=[
                'joint_state_broadcaster',
                '-c', f'/{name}/controller_manager'
            ],
        )
        diff_drive_base_controller_spawner = Node(
            package='controller_manager',
            executable='spawner',
            arguments=[
                'diff_drive_base_controller',
                '--param-file',
                robot_controllers,
                '-c', f'/{name}/controller_manager'
            ],
        )

        launch_description.append(node_robot_state_publisher)
        launch_description.append(gz_spawn_entity)
        launch_description.append(RegisterEventHandler(
            event_handler=OnProcessExit(
                target_action=gz_spawn_entity,
                on_exit=[joint_state_broadcaster_spawner],
            )
        ))
        launch_description.append(RegisterEventHandler(
            event_handler=OnProcessExit(
                target_action=joint_state_broadcaster_spawner,
                on_exit=[diff_drive_base_controller_spawner],
            )
        ))

    spawn_entity('r1', '0', '0', '0')
    spawn_entity('r2', '-4.0', '-1.0', '0')

    # Bridge
    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        parameters=[{
            'config_file': PathJoinSubstitution(
                [
                    FindPackageShare('bargain_bots_demos'),
                    'config',
                    'diff_drive_bridge.yaml',
                ]
            ),
            'qos_overrides./tf_static.publisher.durability': 'transient_local',
        }],
        output='screen'
    )

    ld = LaunchDescription([
        # Launch gazebo environment
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                [PathJoinSubstitution([FindPackageShare('ros_gz_sim'),
                                       'launch',
                                       'gz_sim.launch.py'])]),
            launch_arguments=[('gz_args', [' -r -v 1 world.sdf'])]),
        bridge,
        # Launch Arguments
        DeclareLaunchArgument(
            'use_sim_time',
            default_value=use_sim_time,
            description='If true, use simulated clock'),
        DeclareLaunchArgument(
            'description_format',
            default_value='urdf',
            description='Robot description format to use, urdf or sdf'),
    ] + launch_description)

    return ld
