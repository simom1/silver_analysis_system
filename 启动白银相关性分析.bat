@echo off
chcp 65001 >nul
title 白银相关性分析系统

echo.
echo ========================================
echo    🥈 白银相关性分析系统
echo ========================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未找到Python
    echo 请先安装Python 3.7或更高版本
    echo.
    pause
    exit /b 1
)

REM 检查必要的文件
if not exist "start_silver_analysis.py" (
    echo ❌ 错误: 未找到 start_silver_analysis.py
    echo 请确保所有文件都在同一目录下
    echo.
    pause
    exit /b 1
)

REM 检查MT5包
python -c "import MetaTrader5" >nul 2>&1
if errorlevel 1 (
    echo ⚠️  警告: 未安装MetaTrader5包
    echo 正在尝试安装...
    pip install MetaTrader5
    if errorlevel 1 (
        echo ❌ 安装失败，请手动安装: pip install MetaTrader5
        pause
        exit /b 1
    )
)

REM 启动程序
echo ✅ 环境检查完成，启动分析系统...
echo.
python start_silver_analysis.py

echo.
echo 程序已结束
pause