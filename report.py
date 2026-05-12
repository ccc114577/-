#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Core models and utilities for Robot Navigation Deploy Agent MVP."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable, List, Optional, Sequence
import re


@dataclass
class Diagnosis:
    """One diagnosis item produced by a rule."""

    title: str
    severity: str  # error / warning / info
    confidence: float
    evidence: List[str]
    cause: str
    checks: List[str]
    fixes: List[str]
    commands: List[str]
    files_to_check: List[str] = field(default_factory=list)


@dataclass
class Rule:
    """A text-matching diagnostic rule."""

    name: str
    patterns: List[re.Pattern]
    builder: Callable[[str, List[str]], Diagnosis]

    def match(self, text: str) -> Optional[Diagnosis]:
        hits: List[str] = []
        for pattern in self.patterns:
            for match in pattern.finditer(text):
                line = extract_line(text, match.start())
                if line and line not in hits:
                    hits.append(line)
        if not hits:
            return None
        return self.builder(text, hits[:10])


def compile_patterns(patterns: Sequence[str]) -> List[re.Pattern]:
    return [re.compile(p, re.IGNORECASE | re.MULTILINE) for p in patterns]


def extract_line(text: str, pos: int) -> str:
    start = text.rfind("\n", 0, pos) + 1
    end = text.find("\n", pos)
    if end == -1:
        end = len(text)
    return text[start:end].strip()


def read_input(path: Optional[str] = None, raw_text: Optional[str] = None) -> str:
    if raw_text:
        return raw_text
    if not path:
        raise ValueError("需要通过 --log/--file 指定文件，或通过 --text 输入文本。")
    file_path = Path(path).expanduser()
    if not file_path.exists():
        raise FileNotFoundError(f"文件不存在：{file_path}")
    return file_path.read_text(encoding="utf-8", errors="ignore")


def unique_keep_order(items: Iterable[str]) -> List[str]:
    seen = set()
    result: List[str] = []
    for item in items:
        item = item.strip()
        if item and item not in seen:
            seen.add(item)
            result.append(item)
    return result


def severity_rank(severity: str) -> int:
    return {"error": 0, "warning": 1, "info": 2}.get(severity.lower(), 3)
