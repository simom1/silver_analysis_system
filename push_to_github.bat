@echo off
chcp 65001 >nul
title 白银分析系统 - GitHub推送工具

echo.
echo ========================================
echo 🚀 白银分析系统 GitHub推送工具
echo ========================================
echo.

cd /d "%~dp0"

echo 📁 当前目录: %CD%
echo.

echo 🔍 检查Git状态...
git status
echo.

echo 📝 添加所有更改...
git add .
echo.

echo 💾 提交更改...
set /p commit_msg="请输入提交信息 (直接回车使用默认): "
if "%commit_msg%"=="" (
    set commit_msg=🔧 更新白银分析系统 - 修复导入路径和功能优化
)

git commit -m "%commit_msg%"
echo.

echo 🌐 推送到GitHub...
echo 尝试HTTPS推送...
git remote set-url origin https://github.com/simom1/silver_analysis_system.git
git push origin main

if errorlevel 1 (
    echo.
    echo ⚠️ HTTPS推送失败，尝试SSH推送...
    git remote set-url origin git@github.com:simom1/silver_analysis_system.git
    git push origin main
    
    if errorlevel 1 (
        echo.
        echo ❌ 推送失败！
        echo 请检查：
        echo 1. 网络连接是否正常
        echo 2. GitHub访问权限是否正确
        echo 3. SSH密钥是否配置正确
        echo.
        echo 手动推送命令：
        echo git push origin main
    ) else (
        echo.
        echo ✅ SSH推送成功！
    )
) else (
    echo.
    echo ✅ HTTPS推送成功！
)

echo.
echo 📊 查看远程仓库状态...
git remote -v
echo.

echo 🔗 GitHub仓库地址: https://github.com/simom1/silver_analysis_system
echo.

pause