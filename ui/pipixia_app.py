#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
皮皮虾模拟器 v7.0.0 - Flask + 浏览器方案
使用Flask提供本地HTTP服务，自动打开浏览器，稳定可靠
"""

import os
import sys
import re
import time
import json
import threading
import webbrowser

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from database.manager import DatabaseManager

try:
    from flask import Flask, jsonify, request, send_from_directory
except ImportError:
    print("正在安装Flask...")
    os.system("pip install flask -q")
    from flask import Flask, jsonify, request, send_from_directory


class PipixiaVideoApp:
    def __init__(self):
        self.db = DatabaseManager()
        self.db.init_database()
        self.videos = []
        self.current_index = 0
        self.downloaded_urls = set()
        self._load_downloaded()
        self._load_real_videos()

    def _load_downloaded(self):
        try:
            records = self.db.get_all_downloads()
            self.downloaded_urls = {r.get('url', '') for r in records if r.get('url')}
        except:
            self.downloaded_urls = set()

    def _load_real_videos(self):
        """只加载真实皮皮虾视频，不使用备用视频"""
        import random
        
        real_videos_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'real_pipixia_videos.json')
        self.videos = []
        
        try:
            if os.path.exists(real_videos_file):
                with open(real_videos_file, 'r', encoding='utf-8') as f:
                    real_videos = json.load(f)
                    for v in real_videos:
                        self.videos.append({
                            'id': v.get('id', f'real_{len(self.videos)}'),
                            'title': v.get('title', '皮皮虾热门视频'),
                            'author': v.get('author', '皮皮虾用户'),
                            'video_url': v.get('video_url', ''),
                            'cover_url': v.get('cover_url', ''),
                            'avatar_url': v.get('avatar_url', ''),
                            'hot_comment': v.get('hot_comment', ''),
                            'like_count': v.get('like_count', random.randint(1000, 50000)),
                            'comment_count': v.get('comment_count', random.randint(100, 10000)),
                            'share_count': v.get('share_count', random.randint(50, 5000)),
                            'duration': v.get('duration', random.randint(10, 60)),
                        })
                print(f"加载了 {len(self.videos)} 个真实皮皮虾视频")
        except Exception as e:
            print(f"加载真实视频失败: {e}")
        
        if not self.videos:
            print("暂无真实视频，请点击刷新按钮获取")

    def refresh_real_videos(self, count=20):
        """实时刷新获取新的真实皮皮虾视频 - 使用多API源"""
        import requests
        import random
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        print(f"\n🔄 开始刷新真实视频 (目标: {count}个)...")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1',
        }
        
        videos = []
        lock = threading.Lock()
        
        # 方案1: 使用已知的有效分享链接
        known_urls = [
            "https://h5.pipix.com/s/JQaxYVx/",
            "https://h5.pipix.com/s/hukXsy/",
            "https://h5.pipix.com/s/Yr51R7E/",
            "https://h5.pipix.com/s/JepPPqf/",
            "https://h5.pipix.com/s/JesSVDD/",
            "https://h5.pipix.com/s/6Hkqvc6/",
            "https://h5.pipix.com/s/iUPuLCCV/",
        ]
        
        # 方案2: 使用多个第三方API源
        api_sources = [
            {
                'name': 'bugpk',
                'url_template': 'https://api.bugpk.com/api/pipixia?url={}',
            },
            {
                'name': 'xuemy',
                'url_template': 'https://api.xuemy.cn/api/ppx/?url={}',
            },
        ]
        
        def fetch_from_source(api_source, share_url, index):
            """从指定API源获取视频"""
            try:
                api_url = api_source['url_template'].format(share_url)
                resp = requests.get(api_url, headers=headers, timeout=10)
                
                if resp.status_code == 200:
                    data = resp.json()
                    
                    # 不同API的响应格式不同
                    video_url = ''
                    title = ''
                    author = ''
                    cover = ''
                    avatar = ''
                    
                    if api_source['name'] == 'bugpk':
                        if data.get('code') == 200 and data.get('data'):
                            video_data = data['data']
                            video_url = video_data.get('url', '')
                            title = video_data.get('title', '')
                            author = video_data.get('author', '')
                            cover = video_data.get('cover', '')
                            avatar = video_data.get('avatar', '')
                    elif api_source['name'] == 'xuemy':
                        if data.get('status') == '1':
                            video_url = data.get('url', '')
                            title = data.get('name', '')
                            author = data.get('author', '')
                            cover = data.get('cover', '')
                            avatar = ''
                    
                    if video_url:
                        if not title or title.strip() == '':
                            title = f"皮皮虾热门视频 {index+1}"
                        
                        return {
                            'id': f'real_{index:03d}',
                            'title': title,
                            'author': author or '皮皮虾用户',
                            'video_url': video_url,
                            'share_url': share_url,
                            'cover_url': cover,
                            'avatar_url': avatar,
                            'hot_comment': f"这是{author or '作者'}的精彩作品",
                            'like_count': random.randint(1000, 50000),
                            'comment_count': random.randint(100, 10000),
                            'share_count': random.randint(50, 5000),
                            'duration': random.randint(10, 60),
                        }
            except:
                pass
            return None
        
        # 并发获取视频
        all_tasks = []
        task_index = 0
        
        # 为每个分享链接尝试多个API源
        for url in known_urls:
            for source in api_sources:
                all_tasks.append((source, url, task_index))
                task_index += 1
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {
                executor.submit(fetch_from_source, source, url, idx): (source, url, idx)
                for source, url, idx in all_tasks
            }
            
            for future in as_completed(futures):
                if len(videos) >= count:
                    break
                    
                result = future.result()
                if result:
                    with lock:
                        # 避免重复
                        if result['video_url'] not in [v['video_url'] for v in videos]:
                            videos.append(result)
                            print(f"  ✅ {result['title'][:30]}...")
        
        if videos:
            # 按ID排序
            videos.sort(key=lambda x: x['id'])
            
            self.videos = videos[:count]
            self.current_index = 0
            
            # 保存到文件
            real_videos_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'real_pipixia_videos.json')
            with open(real_videos_file, 'w', encoding='utf-8') as f:
                json.dump(self.videos, f, ensure_ascii=False, indent=2)
            
            print(f"\n✅ 刷新成功！获取了 {len(self.videos)} 个真实皮皮虾视频")
            return {'success': True, 'count': len(self.videos)}
        else:
            print("\n❌ 刷新失败，未获取到视频")
            return {'success': False, 'error': '未获取到视频'}

    def _update_downloaded_status(self, video):
        """更新视频的下载状态"""
        if video['video_url'] in self.downloaded_urls:
            video['downloaded'] = True
        else:
            video['downloaded'] = False

    def get_current_video(self):
        if self.videos:
            video = self.videos[self.current_index % len(self.videos)]
            self._update_downloaded_status(video)
            return video
        return None

    def next_video(self):
        if self.videos:
            self.current_index = (self.current_index + 1) % len(self.videos)
            video = self.videos[self.current_index]
            self._update_downloaded_status(video)
            return video
        return None

    def prev_video(self):
        if self.videos:
            self.current_index = (self.current_index - 1) % len(self.videos)
            video = self.videos[self.current_index]
            self._update_downloaded_status(video)
            return video
        return None

    def download_current_video(self):
        """打开视频URL在浏览器中供用户下载"""
        video = self.get_current_video()
        if not video:
            return {'success': False, 'error': '没有视频'}

        if video.get('downloaded'):
            return {'success': False, 'error': '已下载过'}

        try:
            import webbrowser
            
            video_url = video['video_url']
            
            # 在浏览器中打开视频
            webbrowser.open(video_url)
            
            # 创建下载记录
            try:
                self.db.add_download_record(
                    str(hash(video_url)),
                    video['title'],
                    '皮皮虾',
                    video_url,
                    '待下载'
                )
            except:
                pass
            
            video['downloaded'] = True
            self.downloaded_urls.add(video_url)
            
            return {
                'success': True,
                'message': '视频已在浏览器中打开，请在视频上右键 -> 另存为 即可保存',
                'title': video['title'],
                'hot_comment': video['hot_comment']
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def open_download_folder(self):
        try:
            os.startfile(str(config.DOWNLOAD_DIR))
        except:
            pass


def create_app(video_app):
    app = Flask(__name__, static_folder='static', template_folder='templates')
    
    # 主页路由 - 返回HTML界面
    @app.route('/')
    def index():
        return '''<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>皮皮虾</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
html, body { width: 100%; height: 100%; overflow: hidden; background: #000; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; color: #fff; }

.app-container { width: 100%; height: 100%; max-width: 480px; margin: 0 auto; position: relative; background: #000; }

.top-bar { position: absolute; top: 0; left: 0; right: 0; height: 50px; display: flex; align-items: center; justify-content: center; z-index: 100; background: linear-gradient(rgba(0,0,0,0.5), transparent); }
.top-tab { display: flex; gap: 20px; font-size: 16px; color: rgba(255,255,255,0.6); }
.top-tab span.active { color: #fff; font-weight: bold; font-size: 17px; border-bottom: 2px solid #FFD700; padding-bottom: 3px; }
.refresh-btn { position: absolute; right: 15px; top: 50%; transform: translateY(-50%); width: 35px; height: 35px; display: flex; align-items: center; justify-content: center; background: rgba(255,255,255,0.15); border-radius: 50%; cursor: pointer; font-size: 18px; }
.refresh-btn:hover { background: rgba(255,255,255,0.25); }
.refresh-btn.spinning { animation: spin 1s linear infinite; }

.video-swiper { width: 100%; height: 100%; position: relative; overflow: hidden; }
.video-item { width: 100%; height: 100%; position: absolute; top: 0; left: 0; display: flex; align-items: center; justify-content: center; background: #000; }
.video-item video { width: 100%; height: 100%; object-fit: cover; }

.video-info { position: absolute; bottom: 70px; left: 15px; right: 80px; z-index: 50; }
.author-row { display: flex; align-items: center; margin-bottom: 10px; }
.avatar { width: 40px; height: 40px; border-radius: 50%; background: linear-gradient(135deg, #FF6B6B, #FF8E53); display: flex; align-items: center; justify-content: center; font-size: 18px; margin-right: 10px; }
.author-name { font-size: 16px; font-weight: bold; }
.video-desc { font-size: 14px; line-height: 1.5; margin-bottom: 10px; text-shadow: 0 1px 3px rgba(0,0,0,0.8); }
.comment-preview { display: flex; align-items: center; background: rgba(255,255,255,0.15); border-radius: 20px; padding: 6px 12px; font-size: 12px; color: rgba(255,255,255,0.8); }
.comment-preview::before { content: '�'; margin-right: 5px; }

.side-bar { position: absolute; right: 10px; bottom: 80px; display: flex; flex-direction: column; align-items: center; gap: 18px; z-index: 50; }
.side-item { display: flex; flex-direction: column; align-items: center; }
.side-icon { width: 45px; height: 45px; display: flex; align-items: center; justify-content: center; font-size: 28px; margin-bottom: 3px; }
.side-count { font-size: 11px; color: rgba(255,255,255,0.9); }
.download-icon { background: linear-gradient(135deg, #FF6B6B, #FF8E53); border-radius: 50%; width: 50px; height: 50px; }

.bottom-nav { position: absolute; bottom: 0; left: 0; right: 0; height: 60px; background: rgba(0,0,0,0.95); display: flex; align-items: center; justify-content: space-around; border-top: 1px solid rgba(255,255,255,0.1); z-index: 100; }
.nav-btn { display: flex; flex-direction: column; align-items: center; padding: 8px 12px; color: rgba(255,255,255,0.5); font-size: 10px; cursor: pointer; }
.nav-btn.active { color: #fff; }
.nav-btn-icon { font-size: 24px; margin-bottom: 2px; }

.toast { position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); background: rgba(0,0,0,0.85); color: #fff; padding: 12px 20px; border-radius: 8px; font-size: 14px; z-index: 1000; pointer-events: none; opacity: 0; transition: opacity 0.3s; white-space: nowrap; }
.toast.show { opacity: 1; }

.loading { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 35px; height: 35px; border: 3px solid rgba(255,255,255,0.2); border-top-color: #FFD700; border-radius: 50%; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: translate(-50%, -50%) rotate(360deg); } }

.swipe-tip { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); background: rgba(0,0,0,0.7); color: #fff; padding: 10px 20px; border-radius: 20px; font-size: 13px; pointer-events: none; opacity: 0; transition: opacity 0.3s; z-index: 200; }
.swipe-tip.show { opacity: 1; }
</style>
</head>
<body>
<div class="app-container">
    <div class="top-bar">
        <div class="top-tab">
            <span>关注</span>
            <span class="active">推荐</span>
            <span>热榜</span>
        </div>
        <div class="refresh-btn" id="refreshBtn">🔄</div>
    </div>
    
    <div class="video-swiper" id="swiper">
        <div class="video-item" id="videoItem">
            <div class="loading" id="loading"></div>
            <video id="player" autoplay playsinline loop muted></video>
            <div class="video-info">
                <div class="author-row">
                    <div class="avatar" id="avatar">🎬</div>
                    <div class="author-name" id="author">@作者</div>
                </div>
                <div class="video-desc" id="desc">视频描述...</div>
                <div class="comment-preview" id="comment">热门评论加载中...</div>
            </div>
            <div class="side-bar">
                <div class="side-item">
                    <div class="side-icon">❤️</div>
                    <div class="side-count" id="likes">0</div>
                </div>
                <div class="side-item">
                    <div class="side-icon">💬</div>
                    <div class="side-count" id="comments">0</div>
                </div>
                <div class="side-item">
                    <div class="side-icon">↗️</div>
                    <div class="side-count" id="shares">0</div>
                </div>
                <div class="side-item" id="downloadBtn">
                    <div class="side-icon download-icon">⬇️</div>
                    <div class="side-count">下载</div>
                </div>
            </div>
        </div>
    </div>
    
    <div class="bottom-nav">
        <div class="nav-btn active"><div class="nav-btn-icon">🏠</div><div>首页</div></div>
        <div class="nav-btn"><div class="nav-btn-icon">🎬</div><div>视频</div></div>
        <div class="nav-btn"><div class="nav-btn-icon">➕</div><div>发布</div></div>
        <div class="nav-btn"><div class="nav-btn-icon">�</div><div>消息</div></div>
        <div class="nav-btn" id="folderBtn"><div class="nav-btn-icon">👤</div><div>我的</div></div>
    </div>
    
    <div class="swipe-tip" id="swipeTip"></div>
    <div class="toast" id="toast"></div>
</div>

<script>
(function() {
    var player = document.getElementById('player');
    var loading = document.getElementById('loading');
    var avatar = document.getElementById('avatar');
    var author = document.getElementById('author');
    var desc = document.getElementById('desc');
    var comment = document.getElementById('comment');
    var likes = document.getElementById('likes');
    var comments = document.getElementById('comments');
    var shares = document.getElementById('shares');
    var toast = document.getElementById('toast');
    var swipeTip = document.getElementById('swipeTip');
    var downloadBtn = document.getElementById('downloadBtn');
    var folderBtn = document.getElementById('folderBtn');
    
    var currentVideo = null;
    var touchStartY = 0;
    var isDownloading = false;
    var isRefreshing = false;
    
    function fmt(n) {
        if (n >= 10000) return (n/10000).toFixed(1) + 'w';
        if (n >= 1000) return (n/1000).toFixed(1) + 'k';
        return n.toString();
    }
    
    function showToast(msg, dur) {
        toast.textContent = msg;
        toast.classList.add('show');
        setTimeout(function() { toast.classList.remove('show'); }, dur || 2000);
    }
    
    function showSwipeTip(t) {
        swipeTip.textContent = t;
        swipeTip.classList.add('show');
        setTimeout(function() { swipeTip.classList.remove('show'); }, 600);
    }
    
    function renderVideo(v) {
        if (!v) return;
        currentVideo = v;
        loading.style.display = 'block';
        player.src = v.video_url;
        player.play().catch(function(){});
        author.textContent = '@' + v.author;
        desc.textContent = v.title;
        comment.textContent = v.hot_comment;
        likes.textContent = fmt(v.like_count);
        comments.textContent = fmt(v.comment_count);
        shares.textContent = fmt(v.share_count);
        
        if (v.downloaded) {
            downloadBtn.querySelector('.download-icon').textContent = '✅';
        } else {
            downloadBtn.querySelector('.download-icon').textContent = '⬇️';
        }
        
        player.onloadeddata = function() { loading.style.display = 'none'; };
        player.onerror = function() { loading.style.display = 'none'; showToast('视频加载失败'); };
    }
    
    function loadVideo() {
        fetch('/api/current')
            .then(function(r) { return r.json(); })
            .then(function(v) { if (v) renderVideo(v); });
    }
    
    function nextVideo() {
        fetch('/api/next')
            .then(function(r) { return r.json(); })
            .then(function(v) { if (v) renderVideo(v); showSwipeTip('⬆️ 下一个'); });
    }
    
    function prevVideo() {
        fetch('/api/prev')
            .then(function(r) { return r.json(); })
            .then(function(v) { if (v) renderVideo(v); showSwipeTip('⬇️ 上一个'); });
    }
    
    function downloadVideo() {
        if (isDownloading) return;
        if (currentVideo && currentVideo.downloaded) { showToast('已下载过'); return; }
        
        isDownloading = true;
        downloadBtn.querySelector('.download-icon').textContent = '⏳';
        showToast('⬇️ 下载中...', 1500);
        
        fetch('/api/download')
            .then(function(r) { return r.json(); })
            .then(function(res) {
                isDownloading = false;
                if (res && res.success) {
                    showToast('✅ ' + res.folder);
                    downloadBtn.querySelector('.download-icon').textContent = '✅';
                    if (currentVideo) currentVideo.downloaded = true;
                } else {
                    showToast('❌ ' + (res ? res.error : '失败'));
                    downloadBtn.querySelector('.download-icon').textContent = '⬇️';
                }
            })
            .catch(function() {
                isDownloading = false;
                downloadBtn.querySelector('.download-icon').textContent = '⬇️';
                showToast('下载失败');
            });
    }
    
    downloadBtn.addEventListener('click', downloadVideo);
    folderBtn.addEventListener('click', function() { fetch('/api/open_folder'); showToast('打开下载文件夹'); });
    
    var refreshBtn = document.getElementById('refreshBtn');
    refreshBtn.addEventListener('click', function() {
        if (isRefreshing) return;
        isRefreshing = true;
        refreshBtn.classList.add('spinning');
        showToast('🔄 刷新中...', 2000);
        
        fetch('/api/refresh?count=20')
            .then(function(r) { return r.json(); })
            .then(function(res) {
                isRefreshing = false;
                refreshBtn.classList.remove('spinning');
                if (res && res.success) {
                    showToast('✅ 获取 ' + res.count + ' 个新视频');
                    loadVideo();
                } else {
                    showToast('❌ 刷新失败');
                }
            })
            .catch(function() {
                isRefreshing = false;
                refreshBtn.classList.remove('spinning');
                showToast('刷新失败');
            });
    });
    
    var swiper = document.getElementById('swiper');
    swiper.addEventListener('touchstart', function(e) { touchStartY = e.touches[0].clientY; });
    swiper.addEventListener('touchend', function(e) {
        var diff = touchStartY - e.changedTouches[0].clientY;
        if (Math.abs(diff) > 50) { diff > 0 ? nextVideo() : prevVideo(); }
    });
    
    document.addEventListener('wheel', function(e) {
        if (e.deltaY > 30) nextVideo();
        else if (e.deltaY < -30) prevVideo();
    });
    
    document.addEventListener('keydown', function(e) {
        if (e.key === 'ArrowDown' || e.key === ' ') { e.preventDefault(); nextVideo(); }
        else if (e.key === 'ArrowUp') { e.preventDefault(); prevVideo(); }
        else if (e.key === 'Enter') { downloadVideo(); }
    });
    
    loadVideo();
})();
</script>
</body>
</html>'''

    # API路由
    @app.route('/api/current')
    def api_current():
        video = video_app.get_current_video()
        if video:
            video['index'] = video_app.current_index
            video['total'] = len(video_app.videos)
        return jsonify(video)

    @app.route('/api/next')
    def api_next():
        video = video_app.next_video()
        if video:
            video['index'] = video_app.current_index
            video['total'] = len(video_app.videos)
        return jsonify(video)

    @app.route('/api/prev')
    def api_prev():
        video = video_app.prev_video()
        if video:
            video['index'] = video_app.current_index
            video['total'] = len(video_app.videos)
        return jsonify(video)

    @app.route('/api/download')
    def api_download():
        return jsonify(video_app.download_current_video())

    @app.route('/api/download_proxy')
    def api_download_proxy():
        """代理下载视频，绕过防盗链"""
        video_url = request.args.get('url', '')
        if not video_url:
            return jsonify({'error': '缺少URL参数'}), 400
        
        try:
            import requests as req
            headers = {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1',
                'Referer': 'https://h5.pipix.com/',
                'Accept': '*/*',
                'Accept-Language': 'zh-CN,zh;q=0.9',
                'Connection': 'keep-alive',
            }
            
            resp = req.get(video_url, headers=headers, stream=True, timeout=120)
            
            if resp.status_code == 200:
                def generate():
                    for chunk in resp.iter_content(32768):
                        if chunk:
                            yield chunk
                
                return app.response_class(
                    generate(),
                    mimetype='video/mp4',
                    headers={
                        'Content-Disposition': 'attachment; filename="video.mp4"',
                        'Content-Length': resp.headers.get('Content-Length', ''),
                    }
                )
            else:
                return jsonify({'error': f'下载失败，状态码: {resp.status_code}'}), resp.status_code
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/open_folder')
    def api_open_folder():
        video_app.open_download_folder()
        return jsonify({'success': True})

    @app.route('/api/refresh')
    def api_refresh():
        count = request.args.get('count', 20, type=int)
        result = video_app.refresh_real_videos(count)
        return jsonify(result)

    return app


def main():
    global video_app
    video_app = PipixiaVideoApp()
    
    print("创建Flask应用...")
    flask_app = create_app(video_app)
    
    # 在后台线程中启动Flask
    def run_flask():
        flask_app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)
    
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # 等待Flask启动
    import time
    time.sleep(2)
    
    # 自动打开浏览器
    print("启动浏览器...")
    webbrowser.open('http://127.0.0.1:5000')
    
    print("皮皮虾模拟器已启动，请在浏览器中操作")
    print("按 Ctrl+C 退出")
    
    try:
        # 保持主线程运行
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n退出皮皮虾模拟器")


if __name__ == '__main__':
    main()
