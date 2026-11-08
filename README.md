# basicmicro_driver

ROS 2 driver for a **differential-drive robot** on a Basicmicro
(RoboClaw / MCP) motor controller.

Based on [basicmicro/basicmicro_ros2](https://github.com/basicmicro/basicmicro_ros2):
the original `basicmicro_node.py` is kept, everything not needed for a
differential-drive robot was removed, and a few safety features were added.

## Interfaces

| Name | Type | Description |
|---|---|---|
| `cmd_vel` (sub) | `geometry_msgs/Twist` | `linear.x` (m/s) and `angular.z` (rad/s) |
| `joint_states` (pub) | `sensor_msgs/JointState` | Wheel angles (rad) and speeds (rad/s), 50 Hz |
| `diagnostics` (pub) | `diagnostic_msgs/DiagnosticArray` | Battery, temperatures, connection health, 1 Hz |
| `basicmicro/status` (pub) | `std_msgs/String` | Published when the connection fails |
| `emergency_stop` (srv) | `std_srvs/Trigger` | Stops the motors and ignores `cmd_vel` until cleared |
| `clear_emergency_stop` (srv) | `std_srvs/Trigger` | Accepts `cmd_vel` again; the robot waits for a **new** command |

The joints in `/joint_states` are named `left_wheel_joint` and
`right_wheel_joint`; use the same names in your URDF.

Safety behaviour:

- **Watchdog:** motors stop if no `cmd_vel` arrives for `cmd_vel_timeout` s (0.5 s).
- **Speed limit keeps the curve:** if a wheel would exceed `max_speed`, both
  wheels are scaled down together.
- **Reconnection:** if the connection fails, the driver retries every 2 s.
  Encoders are reset to zero only on the first connection, so wheel positions
  continue after a reconnect.
- **Shutdown:** motors are released on exit, even with a double Ctrl-C.

## Installation

```bash
# Basicmicro library
sudo apt install python3-serial
pip install --user --break-system-packages basicmicro==2.0.10

# Serial port permission (then log out and back in)
sudo usermod -aG dialout $USER

# Download and build
cd ~/ros2_ws/src
git clone https://github.com/sahiedu/basicmicro_driver.git
cd ~/ros2_ws
rosdep install --from-paths src --ignore-src -y
colcon build --packages-select basicmicro_driver
source install/setup.bash
```

## Usage

### Running the node (first test)

```bash
ros2 run basicmicro_driver basicmicro_node --ros-args -p port:=/dev/ttyACM0
```

This uses the code defaults.

### Running the launch file

Starts the driver with the parameters in `config/basicmicro_driver.yaml`:

```bash
ros2 launch basicmicro_driver basicmicro_driver.launch.py
```

The launch file reads the **installed** copy of the YAML, so run
`colcon build` again after editing it.



### Testing (wheels off the ground)

Drive forward at 0.1 m/s:

```bash
ros2 topic pub -r 10 /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.1}, angular: {z: 0.0}}"
```

Spin in place at 1 rad/s:

```bash
ros2 topic pub -r 10 /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.0}, angular: {z: 1.0}}"
```

Press `Ctrl+C` to stop publishing; the watchdog stops the motors within
`cmd_vel_timeout` seconds. `-r 10` keeps sending the command 10 times per
second. With `--once`, the robot moves for only `cmd_vel_timeout` seconds.

Watch the wheels and try the emergency stop:

```bash
ros2 topic echo /joint_states
ros2 service call /emergency_stop std_srvs/srv/Trigger
ros2 service call /clear_emergency_stop std_srvs/srv/Trigger
```

## Parameters

Set your robot's values in `config/basicmicro_driver.yaml`. The node uses the
defaults below for any parameter missing from the file, or when it is started
without a parameter file.

| Parameter | Default | Description |
|---|---|---|
| `port` | `/dev/ttyACM0` | Serial port. A `/dev/serial/by-id/...` path survives replugging |
| `baud` | `38400` | Baud rate |
| `address` | `128` | Controller address (0x80) |
| `wheel_radius` | `0.1` | m |
| `wheel_separation` | `0.3` | m, between wheel centers |
| `encoder_counts_per_rev` | `1000` | Counts per motor turn |
| `gear_ratio` | `1.0` | Motor turns per wheel turn |
| `max_speed` | `2500` | Counts/s per wheel |
| `cmd_vel_timeout` | `0.5` | s without `cmd_vel` before stopping; `0.0` disables |
| `read_timeout` | `0.05` | s to wait for a reply. The library's default is 1 s, which froze the node for about 2 s per lost reply |

The driver uses `encoder_counts_per_rev × gear_ratio` as counts per wheel
turn. If you only know the counts per wheel turn, put it in
`encoder_counts_per_rev` and leave `gear_ratio: 1.0`.

Write decimals as decimals (`1.0`, not `1`): ROS 2 rejects an integer for a
decimal parameter.

Motor mapping: motor 1 = right wheel, motor 2 = left wheel.
