@echo off
chcp 65001 >nul
title 白银分析系统 - 安全上传到GitHub

echo.
echo ========================================
echo 🚀 白银分析系统 - 安全上传到GitHub
echo ========================================
echo.

cd /d "%~dp0"

echo 📁 当前目录: %CD%
echo.

echo 🔧 配置Git用户信息...
git config user.name "simom1"
git config user.email "simom1@users.noreply.github.com"
echo.

echo 📊 检查Git状态...
git status
echo.

echo 📝 添加所有更改...
git add .
echo.

echo 💾 提交更改...
set /p commit_msg="请输入提交信息 (直接回车使用默认): "
if "%commit_msg%"=="" (
    set commit_msg=🔧 白银分析系统更新 - 移除敏感信息并优化功能
)

git commit -m "%commit_msg%"
echo.

echo 🌐 设置远程仓库地址...
git remote set-url origin https://github.com/simom1/silver_analysis_system.git
echo.

echo 📤 推送到GitHub...
echo ⚠️  注意：系统会提示输入GitHub用户名和密码
echo    用户名: simom1
echo    密码: 请使用你的GitHub Personal Access Token
echo.

git push -u origin main

if %errorlevel% equ 0 (
    echo.
    echo ✅ 成功上传到GitHub!
    echo 🌐 仓库地址: https://github.com/simom1/silver_analysis_system
    echo.
    echo 📊 上传内容包括:
    echo    - 修复的核心分析模块
    echo    - 改进的白银相关性分析工具
    echo    - K线形态匹配功能
    echo    - 完整的文档说明
) else (
    echo.
    echo ❌ 上传失败！
    echo 可能的原因:
    echo 1. 网络连接问题
    echo 2. GitHub访问权限问题
    echo 3. 认证信息错误
    echo.
    echo 💡 解决方案:
    echo 1. 检查网络连接
    echo 2. 确认GitHub Personal Access Token有效
    echo 3. 尝试使用SSH方式推送
)

echo.
echo 🔗 相关链接:
echo    GitHub仓库: https://github.com/simom1/silver_analysis_system
echo    文档说明: 查看 上传说明.md 文件
echo.

pause