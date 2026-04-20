# API 接口文档

## 概述

本工具包含以下主要API接口，供二次开发或集成使用。

---

## API 模块 (api/)

### class PipixiaAPI

皮皮虾 API 封装类

#### 构造函数

```python
api = PipixiaAPI()
```

#### 方法

##### extract_item_id(share_url: str) -> str | None

从分享链接中提取视频ID

**参数**:
- `share_url` (str): 皮皮虾分享链接

**返回**:
- 视频ID字符串，提取失败返回None

**示例**:
```python
item_id = api.extract_item_id("https://v.douyin.com/abc/item/7234567890123456789/")
print(item_id)  # "7234567890123456789"
```

---

##### get_video_detail(item_id: str) -> dict

获取视频详细信息

**参数**:
- `item_id` (str): 视频ID

**返回**:
```python
{
    'id': str,           # 视频ID
    'title': str,        # 标题
    'author': str,       # 作者名
    'author_id': str,    # 作者ID
    'video_url': str,    # 无水印视频URL
    'cover_url': str,    # 封面URL
    'like_count': int,   # 点赞数
    'comment_count': int,# 评论数
    'share_count': int,  # 分享数
    'duration': int,     # 时长(秒)
    'error': str         # 如果出错，包含错误信息
}
```

**示例**:
```python
detail = api.get_video_detail("7234567890123456789")
if 'error' not in detail:
    print(f"标题: {detail['title']}")
    print(f"作者: {detail['author']}")
    print(f"视频URL: {detail['video_url']}")
```

---

##### download_video(video_url: str, save_path: str, progress_callback=None) -> bool

下载视频到本地

**参数**:
- `video_url` (str): 视频直链
- `save_path` (str): 保存路径(含文件名)
- `progress_callback` (function, optional): 进度回调函数，签名为 `callback(progress: int)`

**返回**:
- 成功返回True，失败返回False

**示例**:
```python
def on_progress(p):
    print(f"下载进度: {p}%")

success = api.download_video(
    "https://v.douyin.com/xxx",
    "C:/downloads/video.mp4",
    progress_callback=on_progress
)
```

---

## Database 模块 (database/)

### class DatabaseManager

数据库管理类

#### 构造函数

```python
db = DatabaseManager(db_file: str = None)
```

**参数**:
- `db_file` (str, optional): 数据库文件路径，默认使用config中的设置

#### 方法

##### init_database() -> None

初始化数据库表

```python
db.init_database()
```

---

##### is_downloaded(video_id: str) -> bool

检查视频是否已下载

**参数**:
- `video_id` (str): 视频ID

**返回**:
- 已下载返回True，否则返回False

---

##### add_download_record(video_id: str, title: str, author: str, url: str, file_path: str) -> bool

添加下载记录

**参数**:
- `video_id` (str): 视频ID
- `title` (str): 视频标题
- `author` (str): 作者名称
- `url` (str): 视频URL
- `file_path` (str): 本地保存路径

**返回**:
- 成功返回True

---

##### get_download_count() -> int

获取已下载视频数量

```python
count = db.get_download_count()
```

---

##### get_all_downloads() -> List[dict]

获取所有下载记录

**返回**:
```python
[
    {
        'id': str,
        'title': str,
        'author': str,
        'url': str,
        'file_path': str,
        'downloaded_at': str  # "YYYY-MM-DD HH:MM:SS"
    },
    ...
]
```

---

## Utils 模块 (utils/)

### Logger 类

日志记录工具

```python
from utils import Logger

logger = Logger("my_app")
logger.info("信息日志")
logger.warning("警告日志")
logger.error("错误日志")
logger.debug("调试日志")
```

日志文件位置: `logs/{name}_{YYYYMMDD}.log`

---

### file_helper 模块

#### sanitize_filename(filename: str, max_length: int = 50) -> str

清理文件名，移除非法字符

```python
from utils import sanitize_filename

safe = sanitize_filename('test<>file.mp4')
# 结果: "test__file.mp4"
```

---

#### ensure_directory(path: Path) -> Path

确保目录存在，不存在则创建

```python
from pathlib import Path
from utils import ensure_directory

ensure_directory(Path("C:/downloads"))
```

---

#### format_size(size_bytes: int) -> str

格式化文件大小

```python
from utils import format_size

print(format_size(1024))       # "1.0 KB"
print(format_size(1048576))    # "1.0 MB"
print(format_size(1073741824)) # "1.0 GB"
```

---

## Config 模块 (config/)

### 配置项

| 配置项 | 类型 | 说明 |
|--------|------|------|
| `BASE_DIR` | Path | 项目根目录 |
| `DB_FILE` | Path | 数据库文件路径 |
| `DOWNLOAD_DIR` | Path | 下载目录 |
| `LOG_DIR` | Path | 日志目录 |
| `APP_NAME` | str | 应用名称 |
| `APP_VERSION` | str | 版本号 |
| `APP_INFO` | dict | 皮皮虾API参数 |
| `API_URL` | str | API端点 |
| `USER_AGENT` | str | HTTP User-Agent |
| `REQUEST_TIMEOUT` | int | 请求超时(秒) |
| `DOWNLOAD_TIMEOUT` | int | 下载超时(秒) |
| `CHUNK_SIZE` | int | 下载块大小 |

### 函数

##### ensure_dirs() -> None

创建所有必要的目录

```python
import config
config.ensure_dirs()
```

---

##### get_config() -> dict

获取所有配置

```python
cfg = config.get_config()
```
