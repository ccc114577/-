#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/.."

echo "[1/4] Diagnose Open3D error"
python3 -m robot_nav_agent diagnose --log examples/open3d_error.log

echo "[2/4] Diagnose Ego-Planner runtime log"
python3 -m robot_nav_agent diagnose --log examples/ego_planner_runtime.log -o demo_ego_report.md

echo "[3/4] Inspect topics"
python3 -m robot_nav_agent topics --file examples/topics.txt

echo "[4/4] Generate checklist"
python3 -m robot_nav_agent checklist --platform a2w -o demo_checklist.md

echo "Demo finished. Generated demo_ego_report.md and demo_checklist.md"
