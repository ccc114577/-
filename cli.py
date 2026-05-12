#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Markdown rendering utilities."""

from __future__ import annotations

from typing import List, Sequence

from .core import Diagnosis


def bullet(items: Sequence[str]) -> str:
    if not items:
        return "- 无"
    return "\n".join(f"- {x}" for x in items)


def codeblock(lines: Sequence[str]) -> str:
    if not lines:
        return "```bash\n# 无\n```"
    return "```bash\n" + "\n".join(lines) + "\n```"


def render_diagnosis(d: Diagnosis, index: int) -> str:
    return f"""### {index}. [{d.severity.upper()}] {d.title}

**置信度**：{d.confidence:.2f}

**证据**：
{bullet(d.evidence)}

**问题归因**：
{d.cause}

**建议检查**：
{bullet(d.checks)}

**修复建议**：
{bullet(d.fixes)}

**推荐命令**：
{codeblock(d.commands)}

**重点检查文件/目录**：
{bullet(d.files_to_check)}
"""


def render_report(diagnoses: List[Diagnosis], source_name: str = "input") -> str:
    if not diagnoses:
        return f"""# 机器人导航部署 Agent 诊断报告

输入来源：{source_name}

没有命中已有规则。

建议你补充以下信息后重新诊断：
- 完整编译日志或运行日志
- `rostopic list`
- `rostopic echo -n 1 /Odometry_loc/header`
- `rostopic echo -n 1 /pct_path/header`
- `rostopic echo -n 1 /grid_map/occupancy_inflate/header`
- `rosrun tf view_frames` 生成的 TF 关系
"""
    parts = [
        "# 机器人导航部署 Agent 诊断报告",
        f"\n输入来源：{source_name}\n",
        f"共命中 {len(diagnoses)} 个问题。\n",
    ]
    for idx, diagnosis in enumerate(diagnoses, 1):
        parts.append(render_diagnosis(diagnosis, idx))
    return "\n".join(parts)


def render_checklist(platform: str = "a2w") -> str:
    platform_name = platform.upper()
    return f"""# {platform_name} 机器人导航部署 MVP 检查清单

## 1. 基础环境
- [ ] `uname -m` 确认架构：x86_64 或 aarch64。
- [ ] `lsb_release -a` 确认 Ubuntu 版本。
- [ ] ROS1/ROS2 环境不要混 source。
- [ ] Docker 镜像架构与主机一致。

## 2. 雷达与点云
- [ ] Hesai JT128 驱动能启动。
- [ ] 点云话题频率正常：`rostopic hz /cloud_registered` 或对应原始点云话题。
- [ ] 点云 frame_id 与外参配置一致。
- [ ] 前后双雷达时，先确认单雷达正常，再做点云融合。

## 3. 建图与定位
- [ ] Point-LIO 能稳定建图并保存 PCD。
- [ ] FAST-LIO + Open3D 定位输出 `/Odometry_loc`。
- [ ] `/Odometry_loc/header/frame_id` 与规划全局 frame 可通过 TF 连通。
- [ ] `map -> camera_init -> base_link` 或等价 TF 链路稳定。

## 4. 全局规划 PCT/3D-Navi
- [ ] tomogram/pickle 文件生成成功。
- [ ] 起点和终点位于 free space。
- [ ] A* 能输出 `/pct_path`。
- [ ] `/pct_path/header.frame_id` 与 Ego-Planner 使用 frame 一致。

## 5. Ego-Planner 局部规划
- [ ] `flight_type` 与输入模式一致。
- [ ] `/grid_map/occupancy`、`/grid_map/occupancy_inflate` 正常更新。
- [ ] RViz 中能看到 `global_list`、`optimal_list`、`goal_point`。
- [ ] 终点判断适配 A2W：优先使用 XY 容差，不让 z 误差导致反复运动。

## 6. 实机安全
- [ ] 先低速限幅：速度、加速度、角速度均保守设置。
- [ ] 保留急停手段。
- [ ] 先空旷场地测试，再上复杂环境。
- [ ] 上楼梯前降低地面附近膨胀半径，避免踏步被全部膨胀为不可通行。
"""
