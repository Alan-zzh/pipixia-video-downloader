@echo off
cd /d "%~dp0"
title 皮皮虾模拟器 v6.7.0
echo ========================================
echo   皮皮虾模拟器 v6.7.0 启动中...
echo   手机风格刷视频界面
echo ========================================
echo.

python main.py
if errorlevel 1 (
    echo.
    echo [错误] 启动失败，请检查Python环境
    pause
)
