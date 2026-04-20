# 皮皮虾模拟器架构文档

## 版本信息
- **版本**: v6.1.0
- **更新日期**: 2026-04-19
- **架构模式**: 模块化分层设计

---

## 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                        main.py                              │
│                      (入口层)                               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    ui/main_window.py                        │
│                      (表现层)                                │
│    - Tkinter GUI                                            │
│    - 用户交互处理                                            │
│    - 事件分发                                               │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│   api/          │ │   database/     │ │   utils/        │
│   (业务层)      │ │   (数据层)      │ │   (工具层)      │
├─────────────────┤ ├─────────────────┤ ├─────────────────┤
│ PipixiaAPI      │ │ DatabaseManager │ │ Logger          │
│ - extract       │ │ - init          │ │ - info          │
│   _item_id      │ │ - is_downloaded │ │ - warning       │
│ - get_video     │ │ - add_record    │ │ - error         │
│   _detail       │ │ - get_count     │ │ - debug         │
│ - download      │ │                 │ │                 │
│   _video        │ │                 │ │ file_helper     │
│                 │ │                 │ │ - sanitize      │
│                 │ │                 │ │ - ensure_dir    │
│                 │ │                 │ │ - format_size   │
└─────────────────┘ └─────────────────┘ └─────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                       config.py                              │
│                     (配置层)                                 │
│    - 路径配置                                                │
│    - API参数                                                 │
│    - 常量定义                                                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 模块职责

### 1. config.py (配置层)
**职责**: 集中管理所有配置信息

| 配置项 | 说明 |
|--------|------|
| BASE_DIR | 项目根目录 |
| DB_FILE | 数据库文件路径 |
| DOWNLOAD_DIR | 下载目录路径 |
| LOG_DIR | 日志目录路径 |
| APP_NAME/VERSION | 应用名称和版本 |
| APP_INFO | 皮皮虾API固定参数 |
| API_BASE_URL | API端点地址 |
| USER_AGENT | 请求User-Agent |
| REQUEST_TIMEOUT | 请求超时时间 |
| DOWNLOAD_TIMEOUT | 下载超时时间 |
| CHUNK_SIZE | 下载块大小 |
| MAX_RETRY | 最大重试次数 |

**设计原则**: 所有硬编码值集中在此，便于维护和修改

---

### 2. api/ (业务层)
**职责**: 封装皮皮虾API调用逻辑

#### 类: PipixiaAPI

| 方法 | 说明 |
|------|------|
| `__init__` | 初始化会话，生成设备ID |
| `_generate_did` | 生成设备ID (16位数字) |
| `_generate_iid` | 生成安装ID (16位数字) |
| `_generate_x_bogus` | 生成API签名 |
| `extract_item_id(url)` | 从分享链接提取视频ID |
| `get_video_detail(item_id)` | 获取视频详细信息 |
| `_parse_video_data(data)` | 解析API返回的视频数据 |
| `download_video(url, path, callback)` | 下载视频到本地 |

**依赖关系**:
- 使用 `config` 模块获取配置
- 使用 `requests` 库发送HTTP请求

---

### 3. database/ (数据层)
**职责**: 封装数据库操作

#### 类: DatabaseManager

| 方法 | 说明 |
|------|------|
| `__init__` | 连接数据库，加载已下载ID |
| `_get_connection` | 获取数据库连接 |
| `_load_downloaded_ids` | 加载已下载记录到内存 |
| `init_database` | 初始化数据库表 |
| `is_downloaded(video_id)` | 检查是否已下载 |
| `add_download_record(...)` | 添加下载记录 |
| `get_all_downloads` | 获取所有下载记录 |
| `get_download_count` | 获取已下载数量 |
| `clear_all_records` | 清空所有记录 |

**数据库表结构**:
```sql
CREATE TABLE downloads (
    id TEXT PRIMARY KEY,
    title TEXT,
    author TEXT,
    url TEXT,
    file_path TEXT,
    downloaded_at TIMESTAMP
);
```

**设计原则**:
- 使用 `SET` 存储已下载ID，实现O(1)查询
- 自动维护内存缓存，减少数据库查询

---

### 4. utils/ (工具层)
**职责**: 提供通用工具函数

#### Logger 类
| 方法 | 说明 |
|------|------|
| `info(message)` | 记录信息日志 |
| `warning(message)` | 记录警告日志 |
| `error(message)` | 记录错误日志 |
| `debug(message)` | 记录调试日志 |

日志文件: `logs/{name}_{YYYYMMDD}.log`

#### file_helper 模块
| 函数 | 说明 |
|------|------|
| `sanitize_filename(name, max_length)` | 清理文件名，移除非法字符 |
| `ensure_directory(path)` | 确保目录存在 |
| `get_file_size(path)` | 获取文件大小 |
| `format_size(bytes)` | 格式化文件大小显示 |

---

### 5. ui/ (表现层)
**职责**: 封装GUI界面逻辑

#### 类: MainWindow

| 组件 | 说明 |
|------|------|
| `root` | Tkinter根窗口 |
| `url_input` | URL输入文本框 |
| `queue_tree` | 视频队列表格 |
| `log_text` | 日志显示区 |
| `status_var` | 状态栏变量 |

| 方法 | 说明 |
|------|------|
| `_build_ui` | 构建主界面 |
| `_build_input_panel` | 构建输入面板 |
| `_build_control_panel` | 构建控制面板 |
| `_build_queue_panel` | 构建队列面板 |
| `_build_log_panel` | 构建日志面板 |
| `_log(msg)` | 写入日志 |
| `_update_status` | 更新状态栏 |
| `_on_paste` | 粘贴按钮事件 |
| `_on_parse_and_add` | 解析添加事件 |
| `_parse_urls(urls)` | 解析URL线程 |
| `_add_to_queue(video)` | 添加到队列 |
| `_on_download_all` | 下载全部事件 |
| `_download_worker` | 下载工作线程 |
| `_update_progress(vid, p)` | 更新进度 |
| `_on_clear_queue` | 清空队列 |
| `_on_open_folder` | 打开文件夹 |
| `run` | 启动主循环 |

**设计原则**:
- 事件处理使用线程，避免UI阻塞
- 使用 `after()` 方法安全更新UI

---

## 数据流

### 下载流程
```
用户输入URL
    │
    ▼
extract_item_id() 提取ID
    │
    ▼
get_video_detail() 获取详情
    │
    ▼
检查去重 (database.is_downloaded)
    │
    ├─── 已下载 → 跳过
    │
    ▼
添加到队列队列 (video_queue)
    │
    ▼
用户点击下载
    │
    ▼
_download_worker() 线程处理
    │
    ├─── api.download_video() 下载
    │
    ▼
database.add_download_record() 保存记录
    │
    ▼
更新UI (队列状态)
```

---

## 依赖关系图

```
main.py
  └─> config.py
  └─> ui.main_window.MainWindow
        ├─> api.pipixia.PipixiaAPI
        │     └─> config.py
        ├─> database.manager.DatabaseManager
        │     └─> config.py
        └─> utils.file_helper
```

---

## 扩展指南

### 添加新功能

1. **新API支持** (如抖音)
   - 在 `api/` 下创建新模块
   - 实现统一的接口方法
   - 在 `MainWindow` 中添加调用

2. **新工具函数**
   - 在 `utils/` 下添加新模块
   - 遵循现有命名规范

3. **新数据库表**
   - 在 `DatabaseManager` 中添加方法
   - 更新 `init_database()`

### 修改配置

所有可配置项集中在 `config.py`：
- 路径配置
- API参数
- 超时设置
- 日志级别

---

## 版本历史

| 版本 | 日期 | 架构变化 |
|------|------|---------|
| v6.0 | 2026-04-15 | 原始版本，单文件设计 |
| v6.1 | 2026-04-19 | 模块化重构，分层设计 |
