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

echo 🔍 第一步：安全检查...
echo ========================================
call "敏感信息检查.bat"

echo.
echo ⚠️  请确认上述安全检查结果
set /p safety_check="安全检查是否通过？(y/N): "
if /i not "%safety_check%"=="y" (
    echo ❌ 请先处理安全问题再上传
    pause
    exit /b 1
)

echo.
echo 🔧 第二步：配置Git用户信息...
git config user.name "simom1"
git config user.email "simom1@users.noreply.github.com"
echo ✅ Git用户信息配置完成

echo.
echo 📊 第三步：检查Git状态...
git status
echo.

echo 📝 第四步：添加文件到暂存区...
git add .
echo ✅ 文件添加完成

echo.
echo 💾 第五步：提交更改...
set /p commit_msg="请输入提交信息 (直接回车使用默认): "
if "%commit_msg%"=="" (
    set commit_msg=🔧 白银分析系统更新 - 安全版本 %date% %time%
)

git commit -m "%commit_msg%"
echo ✅ 提交完成

echo.
echo 🌐 第六步：设置远程仓库...
git remote set-url origin https://github.com/simom1/silver_analysis_system.git
echo ✅ 远程仓库设置完成

echo.
echo 📤 第七步：推送到GitHub...
echo ========================================
echo ⚠️  注意：系统会提示输入GitHub认证信息
echo    用户名: simom1
echo    密码: 请使用你的GitHub Personal Access Token
echo    (不要在脚本中保存真实的Token！)
echo ========================================
echo.

git push -u origin main

if %errorlevel% equ 0 (
    echo.
    echo ✅ 成功上传到GitHub!
    echo ========================================
    echo 🌐 仓库地址: https://github.com/simom1/silver_analysis_system
    echo.
    echo 📊 上传内容包括:
    echo    ✅ 修复的核心分析模块
    echo    ✅ 改进的白银相关性分析工具
    echo    ✅ K线形态匹配功能
    echo    ✅ 完整的安全检查工具
    echo    ✅ 详细的文档说明
    echo ========================================
) else (
    echo.
    echo ❌ 上传失败！
    echo ========================================
    echo 可能的原因:
    echo 1. 网络连接问题
    echo 2. GitHub访问权限问题
    echo 3. 认证信息错误
    echo 4. 仓库保护规则阻止
    echo.
    echo 💡 解决方案:
    echo 1. 检查网络连接
    echo 2. 确认GitHub Personal Access Token有效
    echo 3. 检查是否有敏感信息被GitHub阻止
    echo 4. 尝试使用SSH方式推送
    echo ========================================
)

echo.
echo 🔗 相关资源:
echo    📖 安全上传指南: 安全上传指南.md
echo    🔍 敏感信息检查: 敏感信息检查.bat
echo    📋 使用说明: 上传说明.md
echo.

pause