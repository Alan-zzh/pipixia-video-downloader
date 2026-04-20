#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import time
import hashlib
import random
import string
import requests
from urllib.parse import urlencode

import config


class PipixiaAPI:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': config.USER_AGENT,
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'X-Requested-With': 'com.sup.android.superb',
            'Referer': 'https://h5.pipix.com/'
        })
        self.did = self._generate_did()
        self.iid = self._generate_iid()

    def _generate_did(self):
        return ''.join(random.choices(string.digits, k=16))

    def _generate_iid(self):
        return ''.join(random.choices(string.digits, k=16))

    def _generate_x_bogus(self, params):
        query = urlencode(sorted(params.items()))
        fake_sign = hashlib.md5(f"{query}salt{time.time()}".encode()).hexdigest()[:21]
        return fake_sign

    def extract_item_id(self, share_url):
        patterns = [
            r'item/(\d+)',
            r'item_id=(\d+)',
            r'/(\d{18,})',
        ]
        for pattern in patterns:
            match = re.search(pattern, share_url)
            if match:
                return match.group(1)

        try:
            resp = self.session.head(share_url, allow_redirects=True, timeout=10)
            final_url = resp.url
            for pattern in patterns:
                match = re.search(pattern, final_url)
                if match:
                    return match.group(1)
        except:
            pass

        return None

    def get_video_detail(self, item_id):
        params = {
            **config.APP_INFO,
            'item_id': item_id,
            'did': self.did,
            'iid': self.iid,
            'ts': int(time.time()),
        }

        params['X-Bogus'] = self._generate_x_bogus(params)

        try:
            url = f"{config.API_URL}/bds/item/detail/"
            resp = self.session.get(url, params=params, timeout=config.REQUEST_TIMEOUT)
            data = resp.json()

            if data.get('status_code') == 0:
                return self._parse_video_data(data.get('data', {}))
            else:
                return {'error': data.get('status_msg', '未知错误')}
        except Exception as e:
            return {'error': str(e)}

    def _parse_video_data(self, data):
        item = data.get('item', {})
        video = item.get('video', {})
        author = item.get('author', {})

        video_url = ''
        if video.get('download_addr'):
            url_list = video['download_addr'].get('url_list', [])
            if url_list:
                video_url = url_list[0]
        elif video.get('play_addr'):
            url_list = video['play_addr'].get('url_list', [])
            if url_list:
                video_url = url_list[0]

        if video_url:
            video_url = re.sub(r'watermark=[^&]*', '', video_url)
            video_url = video_url.replace('&&', '&').rstrip('&')

        return {
            'id': str(item.get('item_id', '')),
            'title': item.get('content', item.get('desc', '无标题')),
            'author': author.get('name', '未知'),
            'author_id': str(author.get('uid', '')),
            'video_url': video_url,
            'cover_url': item.get('cover', {}).get('url_list', [''])[0],
            'like_count': item.get('stats', {}).get('like_count', 0),
            'comment_count': item.get('stats', {}).get('comment_count', 0),
            'share_count': item.get('stats', {}).get('share_count', 0),
            'duration': video.get('duration', 0),
        }

    def download_video(self, video_url, save_path, progress_callback=None):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Linux; Android 10; SM-G9730) AppleWebKit/537.0.36',
                'Accept': '*/*',
                'Range': 'bytes=0-'
            }

            resp = requests.get(video_url, headers=headers, stream=True, timeout=config.DOWNLOAD_TIMEOUT)
            total_size = int(resp.headers.get('content-length', 0))

            downloaded = 0
            with open(save_path, 'wb') as f:
                for chunk in resp.iter_content(chunk_size=config.CHUNK_SIZE):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback and total_size > 0:
                            progress = int(downloaded * 100 / total_size)
                            progress_callback(progress)

            return True
        except Exception as e:
            print(f"Download error: {e}")
            return False
