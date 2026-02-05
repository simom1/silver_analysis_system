@echo off
chcp 65001 >nul
title 清理Git历史中的敏感信息

echo.
echo ========================================
echo 🧹 清理Git历史中的敏感信息
echo ========================================
echo.

cd /d "%~dp0"

echo ⚠️  警告：此操作将重写Git历史记录
echo    这会影响所有包含敏感信息的提交
echo.
set /p confirm="确认继续吗？(y/N): "
if /i not "%confirm%"=="y" (
    echo 操作已取消
    pause
    exit /b
)

echo.
echo 🔍 检查是否存在敏感文件...
if exist "upload_to_github.bat" (
    echo 发现敏感文件: upload_to_github.bat
    del "upload_to_github.bat"
    echo ✅ 已删除敏感文件
)

echo.
echo 📝 添加更改到暂存区...
git add .

echo.
echo 💾 提交清理更改...
git commit -m "🧹 移除敏感信息 - 删除包含GitHub PAT的文件"

echo.
echo 🔄 使用git filter-branch清理历史...
git filter-branch --force --index-filter "git rm --cached --ignore-unmatch upload_to_github.bat" --prune-empty --tag-name-filter cat -- --all

echo.
echo 🗑️  清理备份引用...
git for-each-ref --format="delete %(refname)" refs/original | git update-ref --stdin

echo.
echo 🧹 垃圾回收...
git reflog expire --expire=now --all
git gc --prune=now --aggressive

echo.
echo ✅ 清理完成！
echo.
echo 📤 现在可以安全推送到GitHub...
echo    运行: 安全上传.bat
echo.

pause