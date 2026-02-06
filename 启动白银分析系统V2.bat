@echo off
chcp 65001 >nul
title 白银分析系统V2启动器

echo.
echo ========================================
echo 🥈 白银分析系统 V2 启动器
echo ========================================
echo 版本: v4.1 (改进版)
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

echo 🔍 检查主程序文件...
if not exist "main_launcher_v2.py" (
    echo ❌ 错误: 未找到 main_launcher_v2.py
    echo 请确保所有文件都在同一目录下
    pause
    exit /b 1
)
echo ✅ 文件检查完成
echo.

echo 🚀 启动白银分析系统V2...
echo.

python main_launcher_v2.py

if errorlevel 1 (
    echo.
    echo ❌ 程序运行出错
) else (
    echo.
    echo ✅ 程序正常结束
)
echo.
pause
