import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    pkg_share = get_package_share_directory('basicmicro_driver')
    params_file = os.path.join(pkg_share, 'config', 'basicmicro_driver.yaml')

    # Driver
    driver = Node(
        package='basicmicro_driver',
        executable='basicmicro_node',
        name='basicmicro_driver',
        output='screen',
        parameters=[params_file],
    )

    return LaunchDescription([
        driver,
    ])
