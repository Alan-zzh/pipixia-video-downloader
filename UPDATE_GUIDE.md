# 版本升级指南

## v6.1.0 升级说明

### 主要变更

#### 架构重构
- 将原有的单文件 `皮皮虾v6.py` (526行) 重构为模块化架构
- 新增 5 个模块目录：`api/`、`database/`、`ui/`、`utils/`、`tests/`
- 新增 `config.py` 集中管理配置

#### 文件变更

| 操作 | 文件/目录 | 说明 |
|------|----------|------|
| 新增 | `main.py` | 程序入口 |
| 新增 | `config.py` | 全局配置 |
| 新增 | `api/` | API模块目录 |
| 新增 | `database/` | 数据库模块目录 |
| 新增 | `ui/` | 界面模块目录 |
| 新增 | `utils/` | 工具模块目录 |
| 新增 | `tests/` | 测试模块目录 |
| 修改 | `start.bat` | 更新启动命令 |
| 修改 | `README.md` | 更新文档 |
| 备份 | `backup_v6_original/` | 原始文件备份 |

#### 新增功能
- 完善的日志系统 (`utils/logger.py`)
- 文件名清理工具 (`utils/file_helper.py`)
- 完整的单元测试 (`tests/test_modules.py`)
- 快速测试脚本 (`tests/quick_test.py`)

---

## 从 v6.0 迁移

### 启动方式变更

**旧版 (v6.0)**:
```bash
python 皮皮虾v6.py
```

**新版 (v6.1)**:
```bash
python main.py
```
或双击 `start.bat`

### 数据库兼容
- 数据库格式完全兼容
- 原有的 `data.db` 可继续使用
- 下载历史记录不会丢失

### 配置变更
- 所有硬编码配置移至 `config.py`
- 如需自定义，编辑 `config.py` 即可

---

## 常见问题

### Q: 启动报错 "No module named 'xxx'"
**A**: 运行以下命令安装依赖：
```bash
pip install requests
```

### Q: 原来的下载记录还在吗？
**A**: 是的，`data.db` 文件完全兼容。

### Q: 如何回退到 v6.0？
**A**: 使用 `backup_v6_original/` 目录中的原始文件。

---

## 目录结构对比

### v6.0 (旧)
```
皮皮虾模拟器/
├── 皮皮虾v6.py       # 单文件，526行
├── start.bat         # 指向错误文件
├── ...
```

### v6.1 (新)
```
皮皮虾模拟器/
├── main.py           # 入口
├── config.py         # 配置
├── api/              # API模块
│   ├── __init__.py
│   └── pipixia.py
├── database/         # 数据库模块
│   ├── __init__.py
│   └── manager.py
├── ui/              # 界面模块
│   ├── __init__.py
│   └── main_window.py
├── utils/           # 工具模块
│   ├── __init__.py
│   ├── logger.py
│   └── file_helper.py
├── tests/           # 测试模块
│   ├── test_modules.py
│   └── quick_test.py
├── start.bat        # 已修复
├── README.md        # 已更新
└── ...
```
