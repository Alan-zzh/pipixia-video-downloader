# 皮皮虾视频下载器 (Pipixia Video Downloader)

## 项目简介

皮皮虾视频下载器是一个用于浏览和下载皮皮虾（Pipixia）短视频的Python工具。

**核心功能**：
- 模拟手机浏览器访问皮皮虾
- 浏览真实皮皮虾视频
- 一键下载高清无水印视频
- 自动保存视频标题和作者信息

---

## 技术架构

```
pipixia-video-downloader/
├── api/                      # API模块
│   ├── __init__.py
│   ├── pipixia.py           # 皮皮虾API接口（视频详情、下载）
│   └── pipixia_feed.py      # 视频推荐流API（第三方解析）
├── database/                 # 数据库模块
│   ├── __init__.py
│   └── manager.py           # SQLite数据库管理
├── ui/                       # UI模块
│   ├── __init__.py
│   ├── browser_window.py    # 浏览器窗口（Selenium）
│   ├── main_window.py       # 主窗口
│   └── pipixia_app.py       # Flask Web应用界面
├── utils/                    # 工具模块
│   ├── __init__.py
│   ├── file_helper.py       # 文件工具
│   └── logger.py            # 日志工具
├── config.py                 # 全局配置
├── main.py                   # 主入口
├── start.bat                 # 一键启动脚本（Windows）
├── .env.example              # 配置模板
├── README.md                 # 项目说明
├── ARCHITECTURE.md           # 架构文档
├── BUG_FIX_LOG.md           # 错误修复日志
├── CHANGELOG.md             # 版本更新日志
├── API_DOC.md               # API接口文档
└── UPDATE_GUIDE.md          # 版本升级指南
```

---

## 技术瓶颈与已知问题（重要）

### 核心问题：皮皮虾没有网页版推荐流API

**问题描述**：
- 皮皮虾只在手机APP中提供"上下滑动刷视频"的推荐流功能
- 网页版（h5.pipix.com）没有公开的推荐流API
- 每个视频页面只能显示单个视频，无法像手机APP一样连续刷

**已尝试的方案**：

| 方案 | 状态 | 说明 |
|------|------|------|
| 直接访问h5.pipix.com | ❌ 失败 | 只是官网介绍页面，没有视频流 |
| 分享链接解析 | ❌ 失败 | 固定的链接，无法实时刷新获取新视频 |
| 逆向推荐流API | ❌ 失败 | 皮皮虾没有公开的网页版推荐接口 |
| Selenium模拟手机浏览器 | ✅ 部分成功 | 可以访问单个视频页面并下载 |
| 第三方API解析 | ✅ 部分成功 | 可以解析分享链接获取视频URL |

**当前解决方案**：
1. 使用Selenium模拟iPhone浏览器访问皮皮虾视频页面
2. 通过视频ID池逐个打开视频页面
3. 每个页面可以查看并下载当前视频
4. 点击"下一个"按钮切换到下一个视频

**技术细节**：
- 浏览器：Edge WebDriver
- 设备模拟：iPhone (390x844, deviceScaleFactor: 3)
- User-Agent: `Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X)`
- 视频下载：通过requests库直接下载视频URL

### 待解决的问题

1. **视频池有限**：当前使用固定的视频ID池，无法像手机APP一样无限刷新
2. **无法获取推荐算法**：皮皮虾的推荐算法只在手机APP中可用
3. **API签名验证**：皮皮虾的API使用X-Bogus等签名参数，逆向难度大

### 可能的解决方案

1. **逆向手机APP**：使用Frida等工具逆向皮皮虾APP，获取推荐流API
2. **使用第三方API**：寻找提供皮皮虾视频解析的第三方服务
3. **模拟手机APP请求**：完全模拟手机APP的HTTP请求特征

---

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

---

## 错误修复日志

详细的错误修复记录请查看 [BUG_FIX_LOG.md](BUG_FIX_LOG.md)

---

## 许可证

本项目仅供学习研究使用。
