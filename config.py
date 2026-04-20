#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.absolute()

DB_FILE = BASE_DIR / "data.db"

DOWNLOAD_DIR = BASE_DIR / "downloads"

LOG_DIR = BASE_DIR / "logs"

APP_NAME = "皮皮虾模拟器"
APP_VERSION = "6.1.0"

APP_INFO = {
    'aid': '1319',
    'app_name': 'pipixia',
    'version_code': '500',
    'version_name': '5.0.0',
    'device_platform': 'android',
    'device_type': 'SM-G9730',
    'device_brand': 'samsung',
    'language': 'zh',
    'os_api': '29',
    'os_version': '10',
    'manifest_version_code': '500',
    'resolution': '1080x1920',
    'dpi': '480',
}

API_BASE_URL = "https://h5.pipix.com"
API_URL = "https://is.snssdk.com"

USER_AGENT = 'Mozilla/5.0 (Linux; Android 10; SM-G9730 Build/QP1A.190711.020; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/83.0.4103.106 Mobile Safari/537.36'

REQUEST_TIMEOUT = 15
DOWNLOAD_TIMEOUT = 60
CHUNK_SIZE = 8192

MAX_RETRY = 3
RETRY_DELAY = 2

def ensure_dirs():
    for directory in [DOWNLOAD_DIR, LOG_DIR]:
        directory.mkdir(parents=True, exist_ok=True)

def get_config():
    return {
        'db_file': str(DB_FILE),
        'download_dir': str(DOWNLOAD_DIR),
        'log_dir': str(LOG_DIR),
        'app_name': APP_NAME,
        'app_version': APP_VERSION,
    }
