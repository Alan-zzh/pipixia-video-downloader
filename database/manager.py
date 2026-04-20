#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
from datetime import datetime
from typing import Set, Optional, List, Dict

import config


class DatabaseManager:
    def __init__(self, db_file: Optional[str] = None):
        self.db_file = db_file or config.DB_FILE
        self._downloaded_ids: Set[str] = set()
        self._load_downloaded_ids()

    def _get_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_file)

    def _load_downloaded_ids(self):
        try:
            conn = self._get_connection()
            c = conn.cursor()
            c.execute('SELECT id FROM downloads')
            self._downloaded_ids = {row[0] for row in c.fetchall()}
            conn.close()
        except:
            self._downloaded_ids = set()

    def init_database(self):
        conn = self._get_connection()
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS downloads
                     (id TEXT PRIMARY KEY, title TEXT, author TEXT,
                      url TEXT, file_path TEXT,
                      downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        conn.commit()
        conn.close()

    def is_downloaded(self, video_id: str) -> bool:
        return video_id in self._downloaded_ids

    def add_download_record(self, video_id: str, title: str, author: str,
                           url: str, file_path: str) -> bool:
        try:
            conn = self._get_connection()
            c = conn.cursor()
            c.execute('INSERT OR REPLACE INTO downloads VALUES (?, ?, ?, ?, ?, ?)',
                     (video_id, title, author, url, file_path,
                      datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            conn.commit()
            conn.close()
            self._downloaded_ids.add(video_id)
            return True
        except Exception as e:
            print(f"Database error: {e}")
            return False

    def get_all_downloads(self) -> List[Dict]:
        try:
            conn = self._get_connection()
            c = conn.cursor()
            c.execute('SELECT * FROM downloads ORDER BY downloaded_at DESC')
            rows = c.fetchall()
            conn.close()
            return [
                {
                    'id': row[0],
                    'title': row[1],
                    'author': row[2],
                    'url': row[3],
                    'file_path': row[4],
                    'downloaded_at': row[5]
                }
                for row in rows
            ]
        except:
            return []

    def get_download_count(self) -> int:
        return len(self._downloaded_ids)

    def clear_all_records(self):
        try:
            conn = self._get_connection()
            c = conn.cursor()
            c.execute('DELETE FROM downloads')
            conn.commit()
            conn.close()
            self._downloaded_ids.clear()
            return True
        except:
            return False
