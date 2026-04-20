#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
皮皮虾模拟器 v8.0.0 - 沉浸式手机模拟器
全屏垂直滚动刷视频 + 后端一键静默下载
"""

import os
import sys
import re
import time
import json
import threading
import requests
import webbrowser

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from database.manager import DatabaseManager
from api.pipixia import PipixiaAPI
from api.pipixia_feed import PipixiaFeedFetcher

try:
    from flask import Flask, jsonify, request
except ImportError:
    os.system("pip install flask -q")
    from flask import Flask, jsonify, request


class PipixiaVideoApp:
    def __init__(self):
        self.db = DatabaseManager()
        self.db.init_database()
        self.api = PipixiaAPI()
        self.feed_fetcher = PipixiaFeedFetcher()
        self.videos = []
        self.current_index = 0
        self.download_lock = threading.Lock()
        self._load_videos()

    def _load_videos(self):
        cache_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'video_cache.json')
        try:
            if os.path.exists(cache_file):
                with open(cache_file, 'r', encoding='utf-8') as f:
                    self.videos = json.load(f)
                print(f"加载了 {len(self.videos)} 个缓存视频")
        except Exception as e:
            print(f"加载缓存失败: {e}")

    def _save_cache(self):
        cache_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'video_cache.json')
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.videos, f, ensure_ascii=False, indent=2)
        except:
            pass

    def refresh_videos(self, count=15):
        print(f"\n刷新视频 (目标: {count}个)...")
        new_videos = self.feed_fetcher.fetch_recommend_feed(count=count)
        if new_videos:
            self.videos = new_videos
            self.current_index = 0
            self._save_cache()
            print(f"刷新成功: {len(self.videos)} 个视频")
            return {'success': True, 'count': len(self.videos)}
        return {'success': False, 'error': '未获取到视频'}

    def get_current_video(self):
        if self.videos:
            return self.videos[self.current_index % len(self.videos)]
        return None

    def next_video(self):
        if self.videos:
            self.current_index = (self.current_index + 1) % len(self.videos)
            return self.videos[self.current_index]
        return None

    def prev_video(self):
        if self.videos:
            self.current_index = (self.current_index - 1) % len(self.videos)
            return self.videos[self.current_index]
        return None

    def download_current_video(self):
        video = self.get_current_video()
        if not video:
            return {'success': False, 'error': '没有视频'}

        with self.download_lock:
            video_url = video.get('video_url', '')
            if not video_url:
                return {'success': False, 'error': '视频链接无效'}

            title = video.get('title', '皮皮虾视频')
            author = video.get('author', '未知')
            hot_comment = video.get('hot_comment', '')

            safe_title = re.sub(r'[\\/:*?"<>|]', '_', title)[:50]
            folder_name = f"{safe_title}_{author}"
            save_dir = os.path.join(config.DOWNLOAD_DIR, folder_name)
            os.makedirs(save_dir, exist_ok=True)

            video_path = os.path.join(save_dir, 'video.mp4')
            info_path = os.path.join(save_dir, 'info.txt')

            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1',
                    'Referer': 'https://h5.pipix.com/',
                    'Accept': '*/*',
                }
                resp = requests.get(video_url, headers=headers, stream=True, timeout=60)
                total = int(resp.headers.get('content-length', 0))
                downloaded = 0

                with open(video_path, 'wb') as f:
                    for chunk in resp.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)

                with open(info_path, 'w', encoding='utf-8') as f:
                    f.write(f"标题: {title}\n")
                    f.write(f"作者: {author}\n")
                    f.write(f"热评: {hot_comment}\n")

                try:
                    self.db.add_download_record(
                        str(hash(video_url)),
                        title,
                        '皮皮虾',
                        video_url,
                        '已完成'
                    )
                except:
                    pass

                video['downloaded'] = True
                return {
                    'success': True,
                    'message': '下载完成',
                    'folder': folder_name,
                    'title': title,
                    'author': author,
                    'hot_comment': hot_comment
                }
            except Exception as e:
                return {'success': False, 'error': str(e)}

    def open_download_folder(self):
        try:
            os.startfile(str(config.DOWNLOAD_DIR))
        except:
            pass


def create_app(video_app):
    app = Flask(__name__)

    @app.route('/')
    def index():
        return '''<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>皮皮虾</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;-webkit-tap-highlight-color:transparent}
html,body{width:100%;height:100%;overflow:hidden;background:#000;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;color:#fff}
.app{width:100%;height:100%;max-width:480px;margin:0 auto;position:relative;background:#000}
.top{position:absolute;top:0;left:0;right:0;height:50px;display:flex;align-items:center;justify-content:center;z-index:100;background:linear-gradient(rgba(0,0,0,.5),transparent)}
.tabs{display:flex;gap:20px;font-size:16px;color:rgba(255,255,255,.6)}
.tabs .active{color:#fff;font-weight:700;border-bottom:2px solid #FFD700;padding-bottom:3px}
.refresh{position:absolute;right:15px;top:50%;transform:translateY(-50%);width:35px;height:35px;display:flex;align-items:center;justify-content:center;background:rgba(255,255,255,.15);border-radius:50%;cursor:pointer;font-size:18px}
.refresh:hover{background:rgba(255,255,255,.25)}
.refresh.spin{animation:spin 1s linear infinite}
@keyframes spin{to{transform:translateY(-50%) rotate(360deg)}}
.swiper{width:100%;height:100%;position:relative;overflow:hidden}
.slide{width:100%;height:100%;position:absolute;top:0;left:0;display:flex;align-items:center;justify-content:center;background:#000;transition:transform .3s ease}
.slide video{width:100%;height:100%;object-fit:cover}
.info{position:absolute;bottom:70px;left:15px;right:80px;z-index:50}
.author{display:flex;align-items:center;margin-bottom:10px}
.avatar{width:40px;height:40px;border-radius:50%;background:linear-gradient(135deg,#FF6B6B,#FF8E53);display:flex;align-items:center;justify-content:center;font-size:18px;margin-right:10px}
.name{font-size:16px;font-weight:700}
.desc{font-size:14px;line-height:1.5;margin-bottom:10px;text-shadow:0 1px 3px rgba(0,0,0,.8)}
.comment{display:flex;align-items:center;background:rgba(255,255,255,.15);border-radius:20px;padding:6px 12px;font-size:12px;color:rgba(255,255,255,.8)}
.side{position:absolute;right:10px;bottom:80px;display:flex;flex-direction:column;align-items:center;gap:18px;z-index:50}
.side-item{display:flex;flex-direction:column;align-items:center}
.side-icon{width:45px;height:45px;display:flex;align-items:center;justify-content:center;font-size:28px;margin-bottom:3px}
.side-count{font-size:11px;color:rgba(255,255,255,.9)}
.dl-icon{background:linear-gradient(135deg,#FF6B6B,#FF8E53);border-radius:50%;width:50px;height:50px}
.nav{position:absolute;bottom:0;left:0;right:0;height:60px;background:rgba(0,0,0,.95);display:flex;align-items:center;justify-content:space-around;border-top:1px solid rgba(255,255,255,.1);z-index:100}
.nav-btn{display:flex;flex-direction:column;align-items:center;padding:8px 12px;color:rgba(255,255,255,.5);font-size:10px;cursor:pointer}
.nav-btn.active{color:#fff}
.nav-icon{font-size:24px;margin-bottom:2px}
.toast{position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);background:rgba(0,0,0,.85);color:#fff;padding:12px 20px;border-radius:8px;font-size:14px;z-index:1000;pointer-events:none;opacity:0;transition:opacity .3s;white-space:nowrap}
.toast.show{opacity:1}
.loading{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:35px;height:35px;border:3px solid rgba(255,255,255,.2);border-top-color:#FFD700;border-radius:50%;animation:spin2 .8s linear infinite}
@keyframes spin2{to{transform:translate(-50%,-50%) rotate(360deg)}}
.progress{position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);background:rgba(0,0,0,.9);padding:20px 30px;border-radius:12px;z-index:1000;text-align:center}
.progress-bar{width:200px;height:6px;background:rgba(255,255,255,.2);border-radius:3px;margin-top:10px;overflow:hidden}
.progress-fill{height:100%;background:linear-gradient(90deg,#FF6B6B,#FFD700);width:0%;transition:width .3s}
</style>
</head>
<body>
<div class="app">
<div class="top">
<div class="tabs"><span>关注</span><span class="active">推荐</span><span>热榜</span></div>
<div class="refresh" id="refreshBtn">🔄</div>
</div>
<div class="swiper" id="swiper">
<div class="slide" id="slide">
<div class="loading" id="loading"></div>
<video id="player" autoplay playsinline loop muted></video>
<div class="info">
<div class="author"><div class="avatar" id="avatar">🎬</div><div class="name" id="author">@作者</div></div>
<div class="desc" id="desc">视频描述...</div>
<div class="comment" id="comment">热门评论加载中...</div>
</div>
<div class="side">
<div class="side-item"><div class="side-icon">❤️</div><div class="side-count" id="likes">0</div></div>
<div class="side-item"><div class="side-icon">💬</div><div class="side-count" id="comments">0</div></div>
<div class="side-item"><div class="side-icon">↗️</div><div class="side-count" id="shares">0</div></div>
<div class="side-item" id="dlBtn"><div class="side-icon dl-icon">⬇️</div><div class="side-count">下载</div></div>
</div>
</div>
</div>
<div class="nav">
<div class="nav-btn active"><div class="nav-icon">🏠</div><div>首页</div></div>
<div class="nav-btn"><div class="nav-icon">🎬</div><div>视频</div></div>
<div class="nav-btn"><div class="nav-icon">➕</div><div>发布</div></div>
<div class="nav-btn"><div class="nav-icon">💬</div><div>消息</div></div>
<div class="nav-btn" id="folderBtn"><div class="nav-icon">👤</div><div>我的</div></div>
</div>
<div class="toast" id="toast"></div>
<div class="progress" id="progress" style="display:none">
<div>正在下载...</div>
<div class="progress-bar"><div class="progress-fill" id="progressFill"></div></div>
</div>
</div>
<script>
(function(){
var player=document.getElementById('player');
var loading=document.getElementById('loading');
var author=document.getElementById('author');
var desc=document.getElementById('desc');
var comment=document.getElementById('comment');
var likes=document.getElementById('likes');
var comments=document.getElementById('comments');
var shares=document.getElementById('shares');
var toast=document.getElementById('toast');
var dlBtn=document.getElementById('dlBtn');
var folderBtn=document.getElementById('folderBtn');
var refreshBtn=document.getElementById('refreshBtn');
var progress=document.getElementById('progress');
var progressFill=document.getElementById('progressFill');
var swiper=document.getElementById('swiper');
var slide=document.getElementById('slide');
var touchStartY=0;
var currentVideo=null;
var isDownloading=false;
var isRefreshing=false;
function fmt(n){if(n>=10000)return(n/10000).toFixed(1)+'w';if(n>=1000)return(n/1000).toFixed(1)+'k';return n.toString()}
function showToast(msg){toast.textContent=msg;toast.classList.add('show');setTimeout(function(){toast.classList.remove('show')},2000)}
function renderVideo(v){
if(!v)return;
currentVideo=v;
loading.style.display='block';
player.src=v.video_url;
player.play().catch(function(){});
author.textContent='@'+v.author;
desc.textContent=v.title;
comment.textContent=v.hot_comment;
likes.textContent=fmt(v.like_count);
comments.textContent=fmt(v.comment_count);
shares.textContent=fmt(v.share_count);
dlBtn.querySelector('.dl-icon').textContent=v.downloaded?'✅':'⬇️';
player.onloadeddata=function(){loading.style.display='none'};
player.onerror=function(){loading.style.display='none';showToast('视频加载失败')}
}
function apiCall(url,data){
var opts={method:data?'POST':'GET'};
if(data){opts.headers={'Content-Type':'application/json'};opts.body=JSON.stringify(data)}
return fetch(url,opts).then(function(r){return r.json()})
}
function loadVideo(){
apiCall('/api/current').then(function(data){if(data.success&&data.video)renderVideo(data.video);else showToast('暂无视频')})
}
refreshBtn.addEventListener('click',function(){
if(isRefreshing)return;
isRefreshing=true;
refreshBtn.classList.add('spin');
showToast('正在刷新视频...');
apiCall('/api/refresh').then(function(data){
refreshBtn.classList.remove('spin');
isRefreshing=false;
if(data.success){showToast('刷新成功: '+data.count+'个视频');loadVideo()}
else showToast('刷新失败: '+(data.error||'未知错误'))
})
});
dlBtn.addEventListener('click',function(){
if(isDownloading||!currentVideo)return;
if(currentVideo.downloaded){showToast('已下载过');return}
isDownloading=true;
progress.style.display='block';
progressFill.style.width='0%';
apiCall('/api/download').then(function(data){
progress.style.display='none';
isDownloading=false;
if(data.success){
dlBtn.querySelector('.dl-icon').textContent='✅';
showToast('✅ 已保存: '+data.folder);
}else{showToast('下载失败: '+(data.error||'未知错误'))}
})
});
folderBtn.addEventListener('click',function(){apiCall('/api/open_folder')});
swiper.addEventListener('touchstart',function(e){touchStartY=e.touches[0].clientY});
swiper.addEventListener('touchend',function(e){
var diff=touchStartY-e.changedTouches[0].clientY;
if(Math.abs(diff)>50){
if(diff>0){apiCall('/api/next').then(function(d){if(d.success&&d.video)renderVideo(d.video)})}
else{apiCall('/api/prev').then(function(d){if(d.success&&d.video)renderVideo(d.video)})}
}
});
swiper.addEventListener('wheel',function(e){
e.preventDefault();
if(e.deltaY>0){apiCall('/api/next').then(function(d){if(d.success&&d.video)renderVideo(d.video)})}
else{apiCall('/api/prev').then(function(d){if(d.success&&d.video)renderVideo(d.video)})}
},{passive:false});
document.addEventListener('keydown',function(e){
if(e.key==='ArrowDown'){apiCall('/api/next').then(function(d){if(d.success&&d.video)renderVideo(d.video)})}
else if(e.key==='ArrowUp'){apiCall('/api/prev').then(function(d){if(d.success&&d.video)renderVideo(d.video)})}
});
loadVideo();
})();
</script>
</body>
</html>'''

    @app.route('/api/current')
    def api_current():
        video = video_app.get_current_video()
        if video:
            return jsonify({'success': True, 'video': video})
        return jsonify({'success': False, 'error': '暂无视频'})

    @app.route('/api/next', methods=['POST'])
    def api_next():
        video = video_app.next_video()
        if video:
            return jsonify({'success': True, 'video': video})
        return jsonify({'success': False, 'error': '没有更多视频'})

    @app.route('/api/prev', methods=['POST'])
    def api_prev():
        video = video_app.prev_video()
        if video:
            return jsonify({'success': True, 'video': video})
        return jsonify({'success': False, 'error': '没有更多视频'})

    @app.route('/api/refresh', methods=['POST'])
    def api_refresh():
        result = video_app.refresh_videos()
        return jsonify(result)

    @app.route('/api/download', methods=['POST'])
    def api_download():
        result = video_app.download_current_video()
        return jsonify(result)

    @app.route('/api/open_folder', methods=['POST'])
    def api_open_folder():
        video_app.open_download_folder()
        return jsonify({'success': True})

    return app


def main():
    print("皮皮虾模拟器 v8.0.0 启动中...")
    video_app = PipixiaVideoApp()
    app = create_app(video_app)
    port = 5000
    url = f"http://127.0.0.1:{port}"
    print(f"服务地址: {url}")
    threading.Timer(1.5, lambda: webbrowser.open(url)).start()
    app.run(host='127.0.0.1', port=port, debug=False, use_reloader=False)


if __name__ == '__main__':
    main()
