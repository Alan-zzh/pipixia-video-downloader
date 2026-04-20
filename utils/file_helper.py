#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import os
from pathlib import Path
from typing import Optional


def sanitize_filename(filename: str, max_length: int = 50) -> str:
    safe = re.sub(r'[^\w\u4e00-\u9fff\-\.]+', '_', filename)
    safe = safe[:max_length].strip('_')
    return safe if safe else 'untitled'


def ensure_directory(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_file_size(file_path: str) -> int:
    try:
        return os.path.getsize(file_path)
    except:
        return 0


def format_size(size_bytes: int) -> str:
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"
