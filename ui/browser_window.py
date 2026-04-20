#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import re
import time
import json
import subprocess
import requests
import threading

try:
    from selenium import webdriver
    from selenium.webdriver.edge.options import Options
    from selenium.webdriver.common.by import By
except ImportError:
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'selenium', '-q'])
    from selenium import webdriver
    from selenium.webdriver.edge.options import Options
    from selenium.webdriver.common.by import By

import config
from database.manager import DatabaseManager


class MobileBrowser:
    def __init__(self):
        self.db = DatabaseManager()
        self.db.init_database()
        self.videos = []
        self.downloaded_urls = set()
        self.driver = None
        self._load_downloaded()

    def _load_downloaded(self):
        records = self.db.get_all_downloads()
        self.downloaded_urls = {r['url'] for r in records if r.get('url')}

    def start_browser(self):
        mobile_emulation = {
            "deviceMetrics": {"width": 375, "height": 812, "pixelRatio": 3.0},
            "userAgent": "Mozilla/5.0 (iPhone; CPU iPhone OS 13_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.2 Mobile/15E148 Safari/604.1"
        }

        options = Options()
        options.add_experimental_option("mobileEmulation", mobile_emulation)
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=375,900')

        try:
            self.driver = webdriver.Edge(options=options)
            self.driver.set_window_size(375, 900)
            self.driver.get('https://www.iesdouyin.com/share/video/')
            return True
        except Exception as e:
            print(f"Edge driver error: {e}")
            self.driver = None
            return False

    def find_video_elements(self):
        if not self.driver:
            return []
        videos = []
        try:
            video_elements = self.driver.find_elements(By.TAG_NAME, 'video')
            for video in video_elements:
                try:
                    src = video.get_attribute('src')
                    if src and src.startswith('http') and '.mp4' in src:
                        title = self._extract_title(video)
                        videos.append({'url': src, 'title': title})
                except:
                    pass

            if not videos:
                source_elements = self.driver.find_elements(By.TAG_NAME, 'source')
                for source in source_elements:
                    try:
                        src = source.get_attribute('src')
                        if src and src.startswith('http') and '.mp4' in src:
                            videos.append({'url': src, 'title': '皮皮虾视频'})
                    except:
                        pass
        except:
            pass
        return videos

    def _extract_title(self, video_elem):
        try:
            parent = video_elem.find_element(By.XPATH, "..")
            title_elem = parent.find_elements(By.CSS_SELECTOR, "h3, .title, [class*='title']")
            if title_elem:
                return title_elem[0].text[:50]
        except:
            pass
        return "皮皮虾视频"

    def close(self):
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass

    def download_video(self, url, title):
        if not url or url in self.downloaded_urls:
            return False

        safe_title = re.sub(r'[^\w\u4e00-\u9fff\-]+', '_', title)[:50]
        filename = f"{safe_title}_{int(time.time())}.mp4"
        save_path = config.DOWNLOAD_DIR / filename

        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_6 like Mac OS X) AppleWebKit/605.1.15',
                'Accept': '*/*'
            }
            resp = requests.get(url, headers=headers, stream=True, timeout=60)
            with open(save_path, 'wb') as f:
                for chunk in resp.iter_content(8192):
                    if chunk:
                        f.write(chunk)

            self.db.add_download_record(str(hash(url)), title, '皮皮虾', url, str(save_path))
            self.downloaded_urls.add(url)
            return True
        except Exception as e:
            print(f"Download error: {e}")
            return False


class BrowserApp:
    def __init__(self):
        self.mobile_browser = None
        self.videos = []
        self.browser_opened = False

    def start_browser(self):
        try:
            self.mobile_browser = MobileBrowser()
            if self.mobile_browser.driver:
                self.browser_opened = True
                threading.Thread(target=self._poll_videos, daemon=True).start()
                return "浏览器已启动，请在Edge窗口操作皮皮虾"
            else:
                return "浏览器启动失败，请检查Edge是否安装"
        except Exception as e:
            return f"启动失败: {str(e)}"

    def _poll_videos(self):
        while self.browser_opened and self.mobile_browser and self.mobile_browser.driver:
            try:
                videos = self.mobile_browser.find_video_elements()
                for video in videos:
                    if not any(v['url'] == video['url'] for v in self.videos):
                        self.videos.append(video)
            except:
                pass
            time.sleep(2)

    def get_videos(self):
        return [{'url': v['url'], 'title': v.get('title', '视频'), 'downloaded': v['url'] in (self.mobile_browser.downloaded_urls if self.mobile_browser else set())} for v in self.videos]

    def download_video(self, index):
        if index >= len(self.videos):
            return False
        video = self.videos[index]
        if self.mobile_browser:
            return self.mobile_browser.download_video(video['url'], video['title'])
        return False

    def open_folder(self):
        os.startfile(config.DOWNLOAD_DIR)

    def close_browser(self):
        self.browser_opened = False
        if self.mobile_browser:
            self.mobile_browser.close()


def main():
    app = BrowserApp()

    html = '''<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>皮皮虾下载器</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, sans-serif; background: #1a1a1a; color: #fff; height: 100vh; display: flex; flex-direction: column; }
.header { background: #2d2d2d; padding: 12px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #444; }
h1 { font-size: 16px; color: #FF6B6B; }
button { padding: 8px 14px; border: none; border-radius: 6px; cursor: pointer; font-size: 13px; }
.btn-green { background: #4CAF50; color: white; }
.btn-blue { background: #2196F3; color: white; }
.main-content { flex: 1; display: flex; flex-direction: column; padding: 10px; overflow-y: auto; }
.info-box { background: #252525; padding: 15px; border-radius: 8px; margin-bottom: 10px; font-size: 13px; line-height: 1.6; }
.info-box h3 { color: #FF6B6B; margin-bottom: 8px; }
.video-list { flex: 1; }
.video-item { background: #2d2d2d; border-radius: 8px; padding: 10px; margin-bottom: 8px; }
.video-title { font-size: 13px; margin-bottom: 6px; word-break: break-all; }
.video-url { font-size: 10px; color: #666; word-break: break-all; margin-bottom: 6px; }
.video-footer { display: flex; justify-content: space-between; align-items: center; }
.download-btn { padding: 6px 12px; font-size: 12px; }
.downloaded { background: #666; color: #ccc; cursor: not-allowed; }
.empty { text-align: center; padding: 30px; color: #666; font-size: 13px; }
.status { background: #333; padding: 8px 12px; font-size: 11px; color: #888; }
.note { background: #3a3a3a; padding: 10px; border-radius: 6px; margin-bottom: 10px; font-size: 12px; color: #FFD700; }
</style>
</head>
<body>
<div class="header">
<h1>🦐 皮皮虾视频下载器</h1>
<button class="btn-blue" onclick="openFolder()">📂</button>
</div>
<div class="main-content">
<div class="note">📱 浏览器窗口已打开，请在Edge浏览器中浏览皮皮虾</div>
<div class="info-box">
<h3>📱 使用说明</h3>
<p>1. 点击"启动浏览器"打开手机版浏览器</p>
<p>2. 在浏览器中访问皮皮虾并播放视频</p>
<p>3. 视频会自动出现在下方列表</p>
<p>4. 点击下载按钮保存视频</p>
</div>
<div style="margin-bottom: 10px;">
<button class="btn-green" onclick="startBrowser()">🚀 启动浏览器</button>
<button class="btn-blue" onclick="refreshVideos()">� 刷新列表</button>
<button class="btn-blue" onclick="downloadAll()">📥 下载全部</button>
</div>
<div class="video-list" id="videoList">
<div class="empty">👆 点击启动浏览器开始</div>
</div>
</div>
<div class="status" id="status">就绪</div>

<script>
let videos = [];

function updateList() {
    const container = document.getElementById('videoList');
    if (videos.length === 0) {
        container.innerHTML = '<div class="empty">👆 播放视频后点击刷新列表</div>';
        return;
    }
    container.innerHTML = videos.map((v, i) => {
        const btnClass = v.downloaded ? 'download-btn downloaded' : 'download-btn btn-green';
        const btnText = v.downloaded ? '✓ 已下载' : '⬇️ 下载';
        const disabled = v.downloaded ? 'disabled' : '';
        return '<div class="video-item"><div class="video-title">' + (v.title || '视频') + '</div><div class="video-url">' + (v.url || '').substring(0, 60) + '...</div><div class="video-footer"><button class="' + btnClass + '" ' + disabled + ' onclick="downloadOne(' + i + ')">' + btnText + '</button></div></div>';
    }).join('');
    document.getElementById('status').textContent = '视频: ' + videos.length + ' | 已下载: ' + videos.filter(v=>v.downloaded).length;
}

function startBrowser() {
    document.getElementById('status').textContent = '正在启动浏览器...';
    window.pywebview.api.start_browser().then(function(msg) {
        document.getElementById('status').textContent = msg;
    });
}

function refreshVideos() {
    window.pywebview.api.get_videos().then(function(v) {
        videos = v;
        updateList();
        document.getElementById('status').textContent = '已刷新，找到 ' + videos.length + ' 个视频';
    });
}

function downloadOne(index) {
    window.pywebview.api.download_video(index).then(function(success) {
        if (success) {
            videos[index].downloaded = true;
            updateList();
        }
    });
}

function downloadAll() {
    videos.forEach(function(v, i) { if (!v.downloaded) downloadOne(i); });
}

function openFolder() {
    window.pywebview.api.open_folder();
}

setInterval(refreshVideos, 3000);
</script>
</body>
</html>'''

    try:
        import webview
        window = webview.create_window('🦐 皮皮虾下载器', html=html, width=420, height=750, resizable=True, js_api=app)
        webview.start(debug=True)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        app.close_browser()


if __name__ == '__main__':
    main()
