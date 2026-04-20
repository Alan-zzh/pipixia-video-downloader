# 皮皮虾视频下载器 - 项目说明

## 项目概述

这是一个用于浏览和下载皮皮虾（Pipixia）短视频的Python工具。

## 核心功能

- 模拟手机浏览器访问皮皮虾
- 浏览真实皮皮虾视频
- 一键下载高清无水印视频
- 自动保存视频标题和作者信息

## 技术架构

```
pipixia-video-downloader/
├── api/                      # API模块
│   ├── pipixia.py           # 皮皮虾API接口
│   └── pipixia_feed.py      # 视频推荐流API
├── database/                 # 数据库模块
│   └── manager.py           # SQLite数据库管理
├── ui/                       # UI模块
│   ├── browser_window.py    # 浏览器窗口
│   ├── main_window.py       # 主窗口
│   └── pipixia_app.py       # Flask Web应用
├── utils/                    # 工具模块
│   ├── file_helper.py       # 文件工具
│   └── logger.py            # 日志工具
├── config.py                 # 全局配置
├── main.py                   # 主入口
└── start.bat                 # 一键启动脚本
```

## 技术瓶颈

**核心问题**：皮皮虾没有网页版推荐流API

- 皮皮虾只在手机APP中提供"上下滑动刷视频"的推荐流功能
- 网页版（h5.pipix.com）没有公开的推荐流API
- 每个视频页面只能显示单个视频，无法像手机APP一样连续刷

**当前解决方案**：
1. 使用Selenium模拟iPhone浏览器访问皮皮虾视频页面
2. 通过视频ID池逐个打开视频页面
3. 每个页面可以查看并下载当前视频
4. 点击"下一个"按钮切换到下一个视频

## 安装与使用

### 环境要求

- Python 3.8+
- Edge浏览器
- 依赖库：selenium, flask, requests

### 安装依赖

```bash
pip install selenium flask requests
```

### 运行

```bash
python main.py
```

或双击运行 `start.bat`

## 许可证

本项目仅供学习研究使用。
