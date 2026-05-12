#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Diagnostic rules for ROS/robot navigation deployment."""

from __future__ import annotations

from typing import List
import re

from .core import Diagnosis, Rule, compile_patterns


def d_open3d_missing(_: str, evidence: List[str]) -> Diagnosis:
    return Diagnosis(
        title="Open3DConfig.cmake 未找到",
        severity="error",
        confidence=0.96,
        evidence=evidence,
        cause=(
            "open3d_loc 调用 find_package(Open3D REQUIRED)，但 CMake 没有找到 Open3DConfig.cmake。"
            "常见原因是 Open3D_DIR 没有指向实际安装目录、Open3D 未安装，或 x86_64/aarch64 架构库混用。"
        ),
        checks=[
            "确认当前系统架构：uname -m。",
            "搜索 Open3DConfig.cmake 是否存在。",
            "检查 CMakeLists.txt 中是否写死了错误的 Open3D_DIR。",
            "如果在 Unitree/A2W aarch64 主机上运行，确认 Open3D 是 aarch64 编译产物。",
        ],
        fixes=[
            "若已存在 Open3DConfig.cmake，将 Open3D_DIR 指向其所在目录。",
            "若不存在，在目标架构上安装或编译 Open3D。",
            "不要把 x86_64 的 libOpen3D.so 直接拷贝到 aarch64 主机使用。",
        ],
        commands=[
            "uname -m",
            "find /home /usr /opt -name 'Open3DConfig.cmake' 2>/dev/null",
            "grep -R \"Open3D_DIR\\|find_package(Open3D\" -n ~/nav_ws/src 2>/dev/null",
            "cd ~/nav_ws && catkin_make -DCMAKE_BUILD_TYPE=Release",
        ],
        files_to_check=["~/nav_ws/src/open3d_loc/CMakeLists.txt", "Open3DConfig.cmake 所在目录"],
    )


def d_hesai_sdk_missing(_: str, evidence: List[str]) -> Diagnosis:
    return Diagnosis(
        title="HesaiLidar_SDK_2.0 子模块缺失或路径错误",
        severity="error",
        confidence=0.97,
        evidence=evidence,
        cause=(
            "hesai_ros_driver 通过 add_subdirectory 引入 HesaiLidar_SDK_2.0，"
            "但 SDK 目录内没有 CMakeLists.txt。通常是 Git 子模块未拉取、zip 下载不完整、或驱动版本目录结构不匹配。"
        ),
        checks=[
            "检查 SDK 目录是否为空或缺少 CMakeLists.txt。",
            "确认驱动是 ROS1 还是 ROS2 对应版本。",
            "确认是否通过 git clone --recursive 获取源码。",
        ],
        fixes=[
            "进入 Hesai 驱动目录执行 git submodule update --init --recursive。",
            "重新递归克隆仓库。",
            "若 SDK 单独下载，将 SDK 放到 CMakeLists.txt 指定路径。",
        ],
        commands=[
            "cd ~/unitree_ws/src/HesaiLidar_ROS_2.0 && git submodule update --init --recursive",
            "ls -la ~/unitree_ws/src/HesaiLidar_ROS_2.0/src/driver/HesaiLidar_SDK_2.0",
            "find ~/unitree_ws/src/HesaiLidar_ROS_2.0 -maxdepth 5 -name CMakeLists.txt",
            "cd ~/unitree_ws && colcon build --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release",
        ],
        files_to_check=["~/unitree_ws/src/HesaiLidar_ROS_2.0/CMakeLists.txt"],
    )


def d_cpp_narrowing(_: str, evidence: List[str]) -> Diagnosis:
    return Diagnosis(
        title="C++ narrowing conversion：int 使用 1e10 初始化",
        severity="error",
        confidence=0.95,
        evidence=evidence,
        cause=(
            "代码中存在 int iter_limit_{1e10}; 或类似写法。1e10 是 double 且超过 int 范围，"
            "C++ 列表初始化禁止窄化转换，因此编译失败。"
        ),
        checks=["定位报错文件中 1e10、iter_limit_、invoke_limit_。", "确认变量是否确实需要极大上限。"],
        fixes=[
            "推荐改为 long long iter_limit_{10000000000LL};",
            "或者将上限设置为合理 int，如 100000000，并做参数化。",
        ],
        commands=[
            "grep -R \"1e10\\|iter_limit_\\|invoke_limit_\" -n ~/nav_ws/src/planner/bspline_opt",
            "cd ~/nav_ws && catkin_make -DCMAKE_BUILD_TYPE=Release",
        ],
        files_to_check=["~/nav_ws/src/planner/bspline_opt/include/bspline_opt/gradient_descent_optimizer.h"],
    )


def d_pcl_missing(_: str, evidence: List[str]) -> Diagnosis:
    return Diagnosis(
        title="PCL / pcl_ros 依赖缺失或版本要求不匹配",
        severity="error",
        confidence=0.88,
        evidence=evidence,
        cause=(
            "CMake 无法找到 pcl_ros/PCL，或源码要求的 PCL 版本高于系统提供版本。"
            "ROS Noetic 常见 PCL 版本约为 1.10，某些源码写死 PCL 1.15 会失败。"
        ),
        checks=["确认 ROS 发行版。", "确认 ros-noetic-pcl-ros 和 pcl-conversions 是否安装。", "检查 CMakeLists.txt 中 PCL 最低版本。"],
        fixes=["安装缺失依赖。", "若版本要求过高，评估源码实际 API 后降低 find_package(PCL x.x REQUIRED) 的版本要求。"],
        commands=[
            "source /opt/ros/noetic/setup.bash",
            "rospack find pcl_ros",
            "dpkg -l | grep -E 'pcl|ros-noetic-pcl'",
            "grep -R \"find_package(PCL\" -n ~/nav_ws/src",
            "sudo apt update && sudo apt install -y ros-noetic-pcl-ros ros-noetic-pcl-conversions libpcl-dev",
        ],
    )


def d_image_geometry_missing(_: str, evidence: List[str]) -> Diagnosis:
    return Diagnosis(
        title="image_geometry 依赖缺失",
        severity="error",
        confidence=0.9,
        evidence=evidence,
        cause="构建 ROS2/Humble 包时找不到 image_geometryConfig.cmake，通常是 ros-humble-image-geometry 未安装。",
        checks=["确认是否在 ROS2 Humble 环境。", "检查 /opt/ros/humble/share/image_geometry 是否存在。"],
        fixes=["安装 ros-humble-image-geometry 后重新 colcon build。"],
        commands=[
            "source /opt/ros/humble/setup.bash",
            "ls /opt/ros/humble/share/image_geometry",
            "sudo apt update && sudo apt install -y ros-humble-image-geometry",
            "cd ~/unitree_ws && colcon build --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release",
        ],
    )


def d_arch_mismatch(_: str, evidence: List[str]) -> Diagnosis:
    return Diagnosis(
        title="CPU 架构不匹配风险：x86_64 与 aarch64 混用",
        severity="warning",
        confidence=0.82,
        evidence=evidence,
        cause=(
            "日志或命令显示当前环境与依赖产物可能存在架构差异。A2W/Jetson/Unitree 主机常见 aarch64，"
            "而桌面 Docker 镜像、Open3D/GTSAM/PCL 预编译库可能是 x86_64。"
        ),
        checks=["检查主机架构。", "检查 Docker 镜像架构。", "检查 .so 文件架构。"],
        fixes=["在目标架构重新编译第三方库。", "分别维护 x86_64 与 aarch64 两套镜像/依赖，不要混用。"],
        commands=[
            "uname -m",
            "dpkg --print-architecture",
            "docker image inspect IMAGE_NAME --format '{{.Architecture}}'",
            "file /path/to/libxxx.so",
        ],
    )


def d_docker_tar_invalid(_: str, evidence: List[str]) -> Diagnosis:
    return Diagnosis(
        title="Docker 镜像 tar 包加载失败",
        severity="error",
        confidence=0.86,
        evidence=evidence,
        cause=(
            "docker load 报 invalid tar header 或 blobs/json 缺失，说明 tar 可能不是 docker save 生成的镜像包、"
            "文件传输损坏、被错误解压重打包，或使用了 docker export/import 与 save/load 混用。"
        ),
        checks=["检查 tar 文件大小和完整性。", "用 tar -tf 查看包结构。", "确认来源命令是 docker save 还是 docker export。"],
        fixes=["镜像迁移应使用 docker save -o image.tar IMAGE:TAG，再用 docker load -i image.tar。", "容器文件系统迁移才使用 docker export/import。"],
        commands=[
            "ls -lh /home/unitree/docker/*.tar",
            "tar -tf /home/unitree/docker/IMAGE.tar | head",
            "docker save -o /home/unitree/docker/vsis_nav_latest.tar vsis_nav:latest",
            "docker load -i /home/unitree/docker/vsis_nav_latest.tar",
        ],
    )


def d_gazebo_gl(_: str, evidence: List[str]) -> Diagnosis:
    return Diagnosis(
        title="Docker 内 Gazebo/RViz OpenGL 或 X11 显示异常",
        severity="warning",
        confidence=0.86,
        evidence=evidence,
        cause="Gazebo/RViz GUI 在容器内启动时无法访问主机 X11、GPU 驱动或 GLX，上层表现为 libGL/nouveau/dri3/glx 错误。",
        checks=["确认 DISPLAY 和 XAUTHORITY。", "确认容器是否挂载 /tmp/.X11-unix。", "确认 NVIDIA runtime 或 Mesa/GLX 支持。"],
        fixes=["先允许本机 X11 访问，再以 host network、DISPLAY、X11 socket、GPU 参数启动容器。", "如果只需要仿真服务，可先跑 gzserver，不开 gzclient。"],
        commands=[
            "xhost +local:docker",
            "docker run --gpus all --net=host -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix IMAGE bash",
            "glxinfo -B || true",
            "gzserver --verbose WORLD.world",
        ],
    )


def d_tf_frame_mismatch(_: str, evidence: List[str]) -> Diagnosis:
    return Diagnosis(
        title="TF / frame_id 不一致：map、camera_init、base_link 链路需统一",
        severity="warning",
        confidence=0.84,
        evidence=evidence,
        cause=(
            "导航链路中 /pct_path、/Odometry_loc、/grid_map/occupancy_inflate 等可能使用不同 frame_id。"
            "若 map↔camera_init、base_link 关系不稳定，Ego-Planner 会把路径、障碍物或机器人位姿解释到错误坐标系。"
        ),
        checks=[
            "查看 /pct_path header.frame_id。",
            "查看 /Odometry_loc header.frame_id 和 child_frame_id。",
            "查看 /grid_map/occupancy_inflate header.frame_id。",
            "检查 TF tree 是否存在 map -> camera_init -> base_link 或等价链路。",
        ],
        fixes=[
            "统一规划输入路径、定位里程计、栅格地图的全局 frame。",
            "若定位输出 camera_init 而规划使用 map，需要发布稳定 map↔camera_init TF 或在发布路径时转换 frame。",
        ],
        commands=[
            "rostopic echo -n 1 /pct_path/header",
            "rostopic echo -n 1 /Odometry_loc/header",
            "rostopic echo -n 1 /grid_map/occupancy_inflate/header",
            "rosrun tf view_frames",
            "rosrun tf tf_echo map camera_init",
            "rosrun tf tf_echo camera_init base_link",
        ],
    )


def d_ego_no_response(_: str, evidence: List[str]) -> Diagnosis:
    return Diagnosis(
        title="Ego-Planner 未响应目标点或外部路径",
        severity="warning",
        confidence=0.82,
        evidence=evidence,
        cause=(
            "常见原因包括 flight_type 配置不对应、外部路径话题未发布或 frame 不一致、定位里程计未到达、"
            "目标点落在障碍物/地面膨胀点云中，或 FSM 未进入正确状态。"
        ),
        checks=[
            "确认 flight_type=3 时外部路径话题是否为 planner 订阅的话题。",
            "确认 /pct_path 持续发布且 frame 与规划 frame 一致。",
            "确认 /Odometry_loc 频率正常。",
            "确认 /ego_planner_node/goal_point、global_list、optimal_list 是否有 marker。",
        ],
        fixes=[
            "先用简单直线路径测试外部路径接口。",
            "2D Nav Goal 点击时固定 z 高度，不要使用 RViz grid ground 的 z=0 作为最终规划高度。",
            "将终点到达判断改为 XY 平面容差，适配 A2W 机体较高的场景。",
        ],
        commands=[
            "rostopic hz /Odometry_loc",
            "rostopic hz /pct_path",
            "rostopic echo -n 1 /pct_path/header",
            "rostopic echo -n 1 /move_base_simple/goal",
            "rostopic list | grep ego_planner_node",
        ],
    )


def d_obstacle_inflate_accumulate(_: str, evidence: List[str]) -> Diagnosis:
    return Diagnosis(
        title="膨胀地图障碍物疑似累积不清理",
        severity="warning",
        confidence=0.86,
        evidence=evidence,
        cause=(
            "若 /grid_map/occupancy_inflate 在无新障碍时仍持续保留移动障碍点，通常是地图没有时间衰减、清理半径不足、"
            "局部地图中心/TF 错误，或地面点被错误纳入障碍物。"
        ),
        checks=[
            "对比 /grid_map/occupancy 与 /grid_map/occupancy_inflate 是否同步变化。",
            "检查 grid_map.cpp 中 raycast 清理、local update range、decay_rate/life time 逻辑。",
            "确认点云 frame 与 odom frame 是否一致。",
        ],
        fixes=[
            "加入 obstacle lifespan/decay 机制，超过时间未观测则清除。",
            "降低地面附近的膨胀半径或按高度分层膨胀。",
            "上楼梯场景建议区分地面、踏步、机体安全半径，不要全高度统一膨胀。",
        ],
        commands=[
            "rostopic hz /grid_map/occupancy",
            "rostopic hz /grid_map/occupancy_inflate",
            "rostopic echo -n 1 /grid_map/occupancy_inflate/header",
            "grep -R \"decay\\|inflate\\|occupancy_inflate\\|clear\" -n ~/nav_ws/src/planner",
        ],
    )


def d_last_progress_time(_: str, evidence: List[str]) -> Diagnosis:
    return Diagnosis(
        title="last_progress_time_ 超时：规划进度停滞",
        severity="warning",
        confidence=0.83,
        evidence=evidence,
        cause=(
            "FSM 检测到机器人长时间没有沿轨迹取得有效进展。可能原因是终点容差过小、底盘控制没有跟踪轨迹、"
            "局部目标被障碍物阻塞、地图膨胀过大，或轨迹服务器没有正确输出控制。"
        ),
        checks=["检查 /cmd_vel 或轨迹控制输出。", "检查 final goal 附近是否存在 inflated obstacle。", "检查到达判断是否使用 z 误差导致 A2W 反复调整。"],
        fixes=["增大 XY 到达容差，弱化或取消最终 z 判断。", "降低局部障碍膨胀半径。", "检查底盘控制接口是否正确消费轨迹/速度指令。"],
        commands=[
            "rostopic echo -n 5 /cmd_vel",
            "rostopic echo -n 1 /ego_planner_node/optimal_list",
            "rostopic echo -n 1 /grid_map/occupancy_inflate/header",
            "grep -R \"last_progress_time_\\|reach\\|goal\" -n ~/nav_ws/src/planner/plan_manage",
        ],
    )


def d_pct_astar_failed(_: str, evidence: List[str]) -> Diagnosis:
    return Diagnosis(
        title="PCT/3D-Navi 全局 A* 搜索失败：goal not reachable",
        severity="warning",
        confidence=0.84,
        evidence=evidence,
        cause=(
            "PCT 分层图或 tomogram 中起终点不在同一可达连通域，或者终点落在障碍/未知区域。"
            "也可能是切片高度、地图分辨率、膨胀半径或起终点投影层选择不合理。"
        ),
        checks=["检查起点/终点是否在 free space。", "查看 tomography 生成的 slice_h0、slice_dh、resolution。", "确认 RViz 交互 marker 的 z 值与切片高度匹配。"],
        fixes=["让起点和终点初始同层且位于可通行区域。", "调整切片高度和膨胀半径。", "先在简单地图上验证 A* 和 /pct_path 发布。"],
        commands=[
            "python3 plan.py --scene Building",
            "grep -R \"slice_h0\\|slice_dh\\|resolution\" -n .",
            "rostopic echo -n 1 /pct_path/header",
        ],
    )


def d_contact_mpc(_: str, evidence: List[str]) -> Diagnosis:
    return Diagnosis(
        title="疑似非导航日志：ANSYS Contact MPC 错误",
        severity="info",
        confidence=0.9,
        evidence=evidence,
        cause="输入日志包含 Contact algorithm: MPC approach，更像有限元接触计算问题，不属于 ROS/机器人导航部署问题。",
        checks=["确认是否误把 ANSYS/有限元日志输入到导航 Agent。"],
        fixes=["若确实是有限元接触问题，应切换到有限元接触设置诊断流程；若是导航问题，请输入 ROS/CMake/TF/RViz 日志。"],
        commands=[],
    )


def get_rules() -> List[Rule]:
    return [
        Rule("open3d_missing", compile_patterns([r"Open3DConfig\.cmake", r"Could not find.*Open3D", r"find_package\(Open3D"]), d_open3d_missing),
        Rule("hesai_sdk_missing", compile_patterns([r"HesaiLidar_SDK_2\.0", r"does not contain a CMakeLists\.txt", r"add_subdirectory.*Hesai"]), d_hesai_sdk_missing),
        Rule("cpp_narrowing", compile_patterns([r"narrowing conversion", r"1\.0e\+10", r"iter_limit_\{1e10\}", r"invoke_limit_\{1e10\}"]), d_cpp_narrowing),
        Rule("pcl_missing", compile_patterns([r"pcl_rosConfig\.cmake", r"Could not find.*pcl_ros", r"PCL.*required.*1\.15", r"Could NOT find PCL"]), d_pcl_missing),
        Rule("image_geometry_missing", compile_patterns([r"image_geometryConfig\.cmake", r"Could not find.*image_geometry"]), d_image_geometry_missing),
        Rule("arch_mismatch", compile_patterns([r"aarch64", r"x86_64", r"wrong ELF class", r"Exec format error", r"Architecture"]), d_arch_mismatch),
        Rule("docker_tar_invalid", compile_patterns([r"invalid tar header", r"blobs/json", r"docker-import", r"docker load"]), d_docker_tar_invalid),
        Rule("gazebo_gl", compile_patterns([r"libGL error", r"failed to create dri3 screen", r"failed to load driver: nouveau", r"glx", r"DISPLAY"]), d_gazebo_gl),
        Rule("tf_frame_mismatch", compile_patterns([r"camera_init", r"base_link", r"frame_id", r"TF", r"tf_echo", r"map"]), d_tf_frame_mismatch),
        Rule("ego_no_response", compile_patterns([r"flight_type", r"2D Nav Goal", r"move_base_simple", r"/pct_path", r"goal_point", r"global_list", r"optimal_list"]), d_ego_no_response),
        Rule("obstacle_inflate_accumulate", compile_patterns([r"occupancy_inflate", r"inflated", r"膨胀", r"移动障碍", r"First 3 control points in obstacles"]), d_obstacle_inflate_accumulate),
        Rule("last_progress_time", compile_patterns([r"last_progress_time_", r"progress_time", r"ERROR !+", r"到达目标点", r"来回运动"]), d_last_progress_time),
        Rule("pct_astar_failed", compile_patterns([r"goal node is not reachable", r"A star Failed", r"tomography", r"slice_h0", r"slice_dh"]), d_pct_astar_failed),
        Rule("contact_mpc", compile_patterns([r"Contact algorithm: MPC approach", r"CONTA178"]), d_contact_mpc),
    ]


def diagnose_text(text: str) -> List[Diagnosis]:
    diagnoses = []
    for rule in get_rules():
        item = rule.match(text)
        if item:
            diagnoses.append(item)
    diagnoses.sort(key=lambda d: ({"error": 0, "warning": 1, "info": 2}.get(d.severity, 3), -d.confidence))
    return diagnoses
