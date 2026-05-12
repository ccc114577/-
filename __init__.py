#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Simple inspectors for topic lists and TF text."""

from __future__ import annotations

from typing import Dict, List

REQUIRED_TOPICS = {
    "定位里程计": ["/Odometry_loc", "/odom", "/lio_sam/mapping/odometry"],
    "全局路径": ["/pct_path", "/global_path"],
    "局部地图": ["/grid_map/occupancy", "/grid_map/occupancy_inflate"],
    "目标点": ["/move_base_simple/goal", "/goal_pose", "/goal_pose_3d"],
    "控制输出": ["/cmd_vel", "/planning/pos_cmd", "/accepted_trajectory"],
}


def inspect_topics(text: str) -> str:
    topics = {line.strip() for line in text.splitlines() if line.strip().startswith("/")}
    lines: List[str] = ["# ROS Topic 检查结果\n"]
    for name, candidates in REQUIRED_TOPICS.items():
        found = [t for t in candidates if t in topics]
        if found:
            lines.append(f"- [OK] {name}：{', '.join(found)}")
        else:
            lines.append(f"- [MISSING] {name}：候选 {', '.join(candidates)} 均未发现")
    lines.append("\n## 建议下一步")
    lines.append("- 对关键话题执行 `rostopic hz` 或 `ros2 topic hz`，确认频率。")
    lines.append("- 对 `/Odometry_loc/header`、`/pct_path/header`、`/grid_map/occupancy_inflate/header` 执行 echo，确认 frame_id。")
    return "\n".join(lines)


def inspect_tf(text: str) -> str:
    lower = text.lower()
    lines = ["# TF 文本检查结果\n"]
    for frame in ["map", "camera_init", "odom", "base_link", "lidar", "hesai"]:
        if frame.lower() in lower:
            lines.append(f"- [FOUND] {frame}")
        else:
            lines.append(f"- [CHECK] 未明显发现 {frame}")
    lines.append("\n## 重点判断")
    lines.append("- Ego-Planner、定位里程计、点云地图、全局路径必须能转换到同一个规划 frame。")
    lines.append("- 若 `/Odometry_loc` 是 `camera_init`，而 `/pct_path` 是 `map`，必须存在稳定的 `map <-> camera_init` TF。")
    return "\n".join(lines)
