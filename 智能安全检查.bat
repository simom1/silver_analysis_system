@echo off
chcp 65001 >nul
title 智能敏感信息检查工具

echo.
echo ========================================
echo 🧠 智能敏感信息检查工具
echo ========================================
echo.

cd /d "%~dp0"

echo 📁 当前目录: %CD%
echo.

echo 🔍 开始智能扫描敏感信息...
echo.

set "found_real_issues=0"

echo 1️⃣ 检查真实GitHub PAT令牌...
findstr /r /c:"github_pat_11[A-Za-z0-9_]\{40,\}" *.py *.json *.bat 2>nul | findstr /v /c:"敏感信息检查.bat" | findstr /v /c:"智能安全检查.bat"
if %errorlevel% equ 0 (
    echo ❌ 发现真实GitHub PAT令牌！
    set "found_real_issues=1"
) else (
    echo ✅ 未发现真实GitHub PAT令牌
)

echo.
echo 2️⃣ 检查真实API密钥...
findstr /r /c:"sk-[A-Za-z0-9]\{48\}" *.py *.json 2>nul
if %errorlevel% equ 0 (
    echo ❌ 发现真实OpenAI API密钥！
    set "found_real_issues=1"
) else (
    echo ✅ 未发现真实API密钥
)

echo.
echo 3️⃣ 检查硬编码密码...
findstr /r /c:"password\s*=\s*[\"'][^\"']*[\"']" *.py *.json 2>nul | findstr /v /c:"YOUR_PASSWORD" | findstr /v /c:"your_password" | findstr /v /c:"example"
if %errorlevel% equ 0 (
    echo ❌ 发现硬编码密码！
    set "found_real_issues=1"
) else (
    echo ✅ 未发现硬编码密码
)

echo.
echo 4️⃣ 检查真实数据库连接...
findstr /r /c:"mongodb://[^/]*:[^@]*@" *.py *.json 2>nul
if %errorlevel% equ 0 (
    echo ❌ 发现真实MongoDB连接字符串！
    set "found_real_issues=1"
) else (
    echo ✅ 未发现真实数据库连接
)

echo.
echo 5️⃣ 检查MT5真实账户信息...
findstr /r /c:"login.*[0-9]\{8,\}" *.py *.json 2>nul | findstr /v /c:"YOUR_MT5_LOGIN" | findstr /v /c:"example"
if %errorlevel% equ 0 (
    echo ❌ 发现可能的真实MT5账户！
    set "found_real_issues=1"
) else (
    echo ✅ 未发现真实MT5账户信息
)

echo.
echo 6️⃣ 检查私钥文件...
if exist "*.pem" (
    echo ❌ 发现PEM私钥文件！
    dir *.pem
    set "found_real_issues=1"
) else (
    echo ✅ 未发现PEM私钥文件
)

if exist "*.key" (
    echo ❌ 发现KEY私钥文件！
    dir *.key
    set "found_real_issues=1"
) else (
    echo ✅ 未发现KEY私钥文件
)

echo.
echo ========================================
if %found_real_issues% equ 1 (
    echo ❌ 发现真实敏感信息！请立即处理
    echo.
    echo 🚨 紧急处理步骤：
    echo 1. 立即更改相关密码/密钥
    echo 2. 删除或替换敏感信息
    echo 3. 重新运行此检查
    echo 4. 确认安全后再上传
) else (
    echo ✅ 智能安全检查通过！
    echo.
    echo 🎉 检查结果：
    echo • 无真实GitHub PAT令牌
    echo • 无真实API密钥
    echo • 无硬编码密码
    echo • 无真实数据库连接
    echo • 无真实MT5账户信息
    echo • 无私钥文件
    echo.
    echo 📝 注意：检查工具忽略了以下安全项目：
    echo • 文档中的示例代码
    echo • 检查脚本本身的搜索命令
    echo • .gitignore中的保护规则
    echo • 公开的GitHub仓库地址
    echo.
    echo 🚀 系统可以安全上传到GitHub！
)
echo ========================================

echo.
pause