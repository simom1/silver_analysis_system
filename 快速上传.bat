@echo off
chcp 65001 >nul

echo 🚀 快速上传到GitHub...

cd /d "%~dp0"

git add .
git commit -m "🔧 白银分析系统更新 - %date% %time%"

echo 尝试推送...
git push origin main

if errorlevel 1 (
    echo ❌ 推送失败，请检查网络连接
) else (
    echo ✅ 推送成功！
    echo 🔗 https://github.com/simom1/silver_analysis_system
)

pause