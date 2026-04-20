#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
from pathlib import Path
from datetime import datetime

import config


class Logger:
    def __init__(self, name: str = "pipixia"):
        self.name = name
        config.ensure_dirs()
        self.log_file = config.LOG_DIR / f"{name}_{datetime.now().strftime('%Y%m%d')}.log"

    def _write(self, level: str, message: str):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_line = f"[{timestamp}] [{level}] {message}\n"

        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_line)
        except:
            pass

        print(log_line.strip())

    def info(self, message: str):
        self._write("INFO", message)

    def warning(self, message: str):
        self._write("WARN", message)

    def error(self, message: str):
        self._write("ERROR", message)

    def debug(self, message: str):
        self._write("DEBUG", message)
