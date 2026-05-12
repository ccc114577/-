#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Command line interface."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from .core import read_input
from .rules import diagnose_text
from .report import render_report, render_checklist
from .inspectors import inspect_topics, inspect_tf


def write_or_print(content: str, output: str | None) -> None:
    if output:
        path = Path(output).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        print(f"已输出：{path}")
    else:
        print(content)


def cmd_diagnose(args: argparse.Namespace) -> int:
    try:
        text = read_input(path=args.log, raw_text=args.text)
    except Exception as exc:
        print(f"输入错误：{exc}", file=sys.stderr)
        return 2
    diagnoses = diagnose_text(text)
    source = args.log or "--text"
    report = render_report(diagnoses, source)
    write_or_print(report, args.output)
    return 0 if diagnoses else 1


def cmd_checklist(args: argparse.Namespace) -> int:
    content = render_checklist(args.platform)
    write_or_print(content, args.output)
    return 0


def cmd_topics(args: argparse.Namespace) -> int:
    try:
        text = read_input(path=args.file, raw_text=args.text)
    except Exception as exc:
        print(f"输入错误：{exc}", file=sys.stderr)
        return 2
    write_or_print(inspect_topics(text), args.output)
    return 0


def cmd_tf(args: argparse.Namespace) -> int:
    try:
        text = read_input(path=args.file, raw_text=args.text)
    except Exception as exc:
        print(f"输入错误：{exc}", file=sys.stderr)
        return 2
    write_or_print(inspect_tf(text), args.output)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="robot-nav-agent",
        description="机器人导航部署诊断 Agent MVP：ROS/CMake/Docker/TF/Ego-Planner/PCT 常见问题诊断。",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("diagnose", help="诊断日志或直接输入的报错文本")
    p.add_argument("--log", help="日志文件路径")
    p.add_argument("--text", help="直接输入的报错文本")
    p.add_argument("-o", "--output", help="输出 Markdown 报告路径")
    p.set_defaults(func=cmd_diagnose)

    p = sub.add_parser("checklist", help="生成部署检查清单")
    p.add_argument("--platform", default="a2w", help="平台名称，默认 a2w")
    p.add_argument("-o", "--output", help="输出 Markdown 路径")
    p.set_defaults(func=cmd_checklist)

    p = sub.add_parser("topics", help="检查 rostopic list / ros2 topic list 文本")
    p.add_argument("--file", help="topic list 文件")
    p.add_argument("--text", help="直接输入 topic list 文本")
    p.add_argument("-o", "--output", help="输出 Markdown 路径")
    p.set_defaults(func=cmd_topics)

    p = sub.add_parser("tf", help="检查 TF 文本")
    p.add_argument("--file", help="TF 文本文件")
    p.add_argument("--text", help="直接输入 TF 文本")
    p.add_argument("-o", "--output", help="输出 Markdown 路径")
    p.set_defaults(func=cmd_tf)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
