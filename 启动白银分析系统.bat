@echo off
chcp 65001 >nul
title 白银分析系统启动器

echo.
echo ========================================
echo 🥈 白银分析系统启动器
echo ========================================
echo.

cd /d "%~dp0"

echo 📁 当前目录: %CD%
echo.

echo 🔍 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python未安装或未添加到PATH
    echo 请先安装Python 3.7+
    pause
    exit /b 1
)

python --version
echo ✅ Python环境正常
echo.

echo 🚀 启动白银分析系统主程序...
echo.

python main_launcher.py

echo.
echo 📊 程序已结束
pause