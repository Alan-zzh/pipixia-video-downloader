#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import time
import threading
from datetime import datetime
from typing import List, Dict, Optional

import tkinter as tk
from tkinter import messagebox, ttk, scrolledtext

import config
from api.pipixia import PipixiaAPI
from database.manager import DatabaseManager
from utils.file_helper import sanitize_filename


class MainWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(f"{config.APP_NAME} v{config.APP_VERSION}")
        self.root.geometry("900x700")
        self.root.configure(bg="#1a1a1a")

        self.api = PipixiaAPI()
        self.db = DatabaseManager()
        self.db.init_database()

        self.video_queue: List[Dict] = []
        self.downloaded_ids: set = self.db._downloaded_ids.copy()
        self.current_downloads: Dict[str, bool] = {}

        self._build_ui()
        self._log("系统启动成功")
        self._log(f"已加载 {len(self.downloaded_ids)} 条下载记录")

    def _build_ui(self):
        tk.Label(
            self.root,
            text=f"🦐 {config.APP_NAME} v{config.APP_VERSION}",
            font=("Microsoft YaHei", 20, "bold"),
            fg="#FF6B6B", bg="#1a1a1a"
        ).pack(pady=10)

        tk.Label(
            self.root,
            text="纯 API 逆向方案 - 无需浏览器",
            font=("Microsoft YaHei", 10),
            fg="#888", bg="#1a1a1a"
        ).pack()

        main = tk.Frame(self.root, bg="#1a1a1a")
        main.pack(fill="both", expand=True, padx=15, pady=10)

        left = tk.Frame(main, bg="#2d2d2d", width=400)
        left.pack(side="left", fill="y", padx=5)
        left.pack_propagate(False)

        self._build_input_panel(left)
        self._build_control_panel(left)

        right = tk.Frame(main, bg="#2d2d2d")
        right.pack(side="right", fill="both", expand=True, padx=5)

        self._build_queue_panel(right)
        self._build_log_panel(right)

        self.status_var = tk.StringVar(value="就绪 | 队列: 0 | 已下载: 0")
        tk.Label(
            self.root,
            textvariable=self.status_var,
            font=("Microsoft YaHei", 10),
            fg="#ccc",
            bg="#333",
            anchor="w"
        ).pack(fill="x", side="bottom")

    def _build_input_panel(self, parent):
        frame = tk.LabelFrame(
            parent,
            text="🔗 添加视频",
            font=("Microsoft YaHei", 12, "bold"),
            fg="white", bg="#2d2d2d"
        )
        frame.pack(fill="x", padx=10, pady=10)

        tk.Label(
            frame,
            text="粘贴皮皮虾分享链接:",
            fg="#ccc", bg="#2d2d2d",
            font=("Microsoft YaHei", 10)
        ).pack(anchor="w", padx=10, pady=5)

        self.url_input = scrolledtext.ScrolledText(
            frame, height=5,
            font=("Consolas", 10),
            bg="#1a1a1a", fg="#00FF00"
        )
        self.url_input.pack(fill="x", padx=10, pady=5)

        btn_frame = tk.Frame(frame, bg="#2d2d2d")
        btn_frame.pack(fill="x", padx=10, pady=5)

        tk.Button(
            btn_frame,
            text="➕ 解析并添加",
            command=self._on_parse_and_add,
            bg="#4CAF50", fg="white",
            font=("Microsoft YaHei", 11),
            height=2
        ).pack(side="left", fill="x", expand=True, padx=2)

        tk.Button(
            btn_frame,
            text="📋 粘贴",
            command=self._on_paste,
            bg="#2196F3", fg="white",
            font=("Microsoft YaHei", 10)
        ).pack(side="right", padx=2)

    def _build_control_panel(self, parent):
        frame = tk.LabelFrame(
            parent,
            text="⬇️ 下载控制",
            font=("Microsoft YaHei", 12, "bold"),
            fg="white", bg="#2d2d2d"
        )
        frame.pack(fill="x", padx=10, pady=10)

        tk.Button(
            frame,
            text="📥 下载全部队列",
            command=self._on_download_all,
            bg="#FF6B6B", fg="white",
            font=("Microsoft YaHei", 12, "bold"),
            height=2
        ).pack(fill="x", padx=10, pady=10)

        ctrl_frame = tk.Frame(frame, bg="#2d2d2d")
        ctrl_frame.pack(fill="x", padx=10, pady=5)

        tk.Button(
            ctrl_frame,
            text="🗑️ 清空队列",
            command=self._on_clear_queue,
            bg="#f44336", fg="white",
            font=("Microsoft YaHei", 10)
        ).pack(side="left", fill="x", expand=True, padx=2)

        tk.Button(
            ctrl_frame,
            text="📂 打开文件夹",
            command=self._on_open_folder,
            bg="#666", fg="white",
            font=("Microsoft YaHei", 10)
        ).pack(side="right", fill="x", expand=True, padx=2)

    def _build_queue_panel(self, parent):
        frame = tk.LabelFrame(
            parent,
            text="📥 视频队列",
            font=("Microsoft YaHei", 12, "bold"),
            fg="white", bg="#2d2d2d"
        )
        frame.pack(fill="both", expand=True, padx=10, pady=5)

        columns = ('title', 'author', 'status', 'progress')
        self.queue_tree = ttk.Treeview(frame, columns=columns, show='headings')
        self.queue_tree.heading('title', text='标题')
        self.queue_tree.heading('author', text='作者')
        self.queue_tree.heading('status', text='状态')
        self.queue_tree.heading('progress', text='进度')
        self.queue_tree.column('title', width=200)
        self.queue_tree.column('author', width=80)
        self.queue_tree.column('status', width=60)
        self.queue_tree.column('progress', width=60)

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.queue_tree.yview)
        self.queue_tree.configure(yscrollcommand=scrollbar.set)

        self.queue_tree.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar.pack(side="right", fill="y")

    def _build_log_panel(self, parent):
        frame = tk.LabelFrame(
            parent,
            text="📝 运行日志",
            font=("Microsoft YaHei", 12, "bold"),
            fg="white", bg="#2d2d2d"
        )
        frame.pack(fill="x", padx=10, pady=5)

        self.log_text = scrolledtext.ScrolledText(
            frame, height=8,
            bg="#1a1a1a", fg="#00FF00",
            font=("Consolas", 9)
        )
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)

    def _log(self, msg: str):
        self.log_text.insert("end", f"[{time.strftime('%H:%M:%S')}] {msg}\n")
        self.log_text.see("end")
        self._update_status()

    def _update_status(self):
        self.status_var.set(
            f"就绪 | 队列: {len(self.video_queue)} | 已下载: {len(self.downloaded_ids)}"
        )

    def _on_paste(self):
        try:
            import pyperclip
            text = pyperclip.paste()
            self.url_input.delete('1.0', 'end')
            self.url_input.insert('1.0', text)
        except:
            self._log("⚠️ 请手动粘贴 (运行: pip install pyperclip)")

    def _on_parse_and_add(self):
        text = self.url_input.get('1.0', 'end').strip()
        if not text:
            messagebox.showwarning("提示", "请输入链接")
            return

        urls = re.findall(r'https?://[^\s\n]+', text)
        if not urls:
            messagebox.showwarning("提示", "未找到有效链接")
            return

        self._log(f"找到 {len(urls)} 个链接，开始解析...")
        threading.Thread(target=self._parse_urls, args=(urls,), daemon=True).start()

    def _parse_urls(self, urls: List[str]):
        for url in urls:
            item_id = self.api.extract_item_id(url)
            if not item_id:
                self.root.after(0, lambda u=url: self._log(f"❌ 无法解析: {u[:50]}..."))
                continue

            self.root.after(0, lambda i=item_id: self._log(f"🔍 解析 item_id: {i}"))

            video_data = self.api.get_video_detail(item_id)

            if 'error' in video_data:
                self.root.after(0, lambda e=video_data['error']: self._log(f"❌ 获取失败: {e}"))
                continue

            if not video_data.get('video_url'):
                self.root.after(0, lambda: self._log("⚠️ 未找到视频链接"))
                continue

            vid = video_data['id']
            if vid in self.downloaded_ids:
                self.root.after(0, lambda: self._log("⚠️ 已下载过，跳过"))
                continue

            exists = any(v.get('id') == vid for v in self.video_queue)
            if exists:
                self.root.after(0, lambda: self._log("⚠️ 已在队列中"))
                continue

            self.root.after(0, lambda v=video_data: self._add_to_queue(v))
            time.sleep(0.5)

    def _add_to_queue(self, video_data: Dict):
        self.video_queue.append(video_data)

        title = video_data.get('title', '无标题')[:25]
        author = video_data.get('author', '未知')[:10]

        self.queue_tree.insert('', 'end', iid=video_data['id'],
                              values=(title, author, '待下载', '0%'))

        self._log(f"✅ 已添加: {title}")
        self._update_status()

    def _on_download_all(self):
        if not self.video_queue:
            messagebox.showinfo("提示", "队列为空")
            return

        config.ensure_dirs()
        threading.Thread(target=self._download_worker, daemon=True).start()

    def _download_worker(self):
        for video in self.video_queue[:]:
            vid = video.get('id')
            if vid in self.downloaded_ids or vid in self.current_downloads:
                continue

            self.current_downloads[vid] = True

            title = video.get('title', '无标题')[:30]
            self.root.after(0, lambda v=vid: self.queue_tree.item(v, values=(
                *self.queue_tree.item(v, 'values')[:2], '下载中', '0%'
            )))
            self.root.after(0, lambda t=title: self._log(f"⬇️ 开始下载: {t}..."))

            safe_title = sanitize_filename(title)
            filename = f"{safe_title}_{vid[-8:]}.mp4"
            save_path = config.DOWNLOAD_DIR / filename

            video_url = video.get('video_url', '')
            if video_url:
                success = self.api.download_video(
                    video_url,
                    str(save_path),
                    progress_callback=lambda p, v=vid: self.root.after(0, lambda: self._update_progress(v, p))
                )

                if success:
                    self.db.add_download_record(
                        vid,
                        video.get('title', ''),
                        video.get('author', ''),
                        video_url,
                        str(save_path)
                    )

                    self.downloaded_ids.add(vid)
                    self.video_queue.remove(video)

                    self.root.after(0, lambda v=vid: self.queue_tree.item(v, values=(
                        *self.queue_tree.item(v, 'values')[:2], '完成', '100%'
                    )))
                    self.root.after(0, lambda f=filename: self._log(f"✅ 下载完成: {f}"))
                else:
                    self.root.after(0, lambda v=vid: self.queue_tree.item(v, values=(
                        *self.queue_tree.item(v, 'values')[:2], '失败', '-'
                    )))
                    self.root.after(0, lambda: self._log("❌ 下载失败"))

            del self.current_downloads[vid]
            time.sleep(1)

    def _update_progress(self, vid: str, progress: int):
        try:
            values = self.queue_tree.item(vid, 'values')
            self.queue_tree.item(vid, values=(*values[:2], '下载中', f'{progress}%'))
        except:
            pass

    def _on_clear_queue(self):
        for vid in [v['id'] for v in self.video_queue]:
            try:
                self.queue_tree.delete(vid)
            except:
                pass
        self.video_queue.clear()
        self._log("🗑️ 队列已清空")
        self._update_status()

    def _on_open_folder(self):
        config.ensure_dirs()
        os.startfile(config.DOWNLOAD_DIR)

    def run(self):
        self._log(f"{config.APP_NAME} v{config.APP_VERSION} 已就绪")
        self._log("粘贴分享链接，点击「解析并添加」")
        self.root.mainloop()


if __name__ == '__main__':
    app = MainWindow()
    app.run()
