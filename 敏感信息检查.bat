@echo off
chcp 65001 >nul
title 敏感信息安全检查工具

echo.
echo ========================================
echo 🔍 敏感信息安全检查工具
echo ========================================
echo.

cd /d "%~dp0"

echo 📁 当前目录: %CD%
echo.

echo 🔍 开始扫描敏感信息...
echo.

set "found_issues=0"

echo 1️⃣ 检查GitHub Personal Access Token...
findstr /r /c:"github_pat_[0-9A-Za-z_]*" *.* >nul 2>&1
if %errorlevel% equ 0 (
    echo ❌ 发现GitHub PAT令牌！
    findstr /r /c:"github_pat_[0-9A-Za-z_]*" *.*
    set "found_issues=1"
) else (
    echo ✅ 未发现GitHub PAT令牌
)

echo.
echo 2️⃣ 检查API密钥...
findstr /r /c:"api[_-]key" *.* >nul 2>&1
if %errorlevel% equ 0 (
    echo ❌ 发现API密钥！
    findstr /r /c:"api[_-]key" *.*
    set "found_issues=1"
) else (
    echo ✅ 未发现API密钥
)

echo.
echo 3️⃣ 检查密码字段...
findstr /r /c:"password.*=" *.* >nul 2>&1
if %errorlevel% equ 0 (
    echo ❌ 发现密码字段！
    findstr /r /c:"password.*=" *.*
    set "found_issues=1"
) else (
    echo ✅ 未发现密码字段
)

echo.
echo 4️⃣ 检查私钥文件...
if exist "*.pem" (
    echo ❌ 发现PEM私钥文件！
    dir *.pem
    set "found_issues=1"
) else (
    echo ✅ 未发现PEM私钥文件
)

if exist "*.key" (
    echo ❌ 发现KEY私钥文件！
    dir *.key
    set "found_issues=1"
) else (
    echo ✅ 未发现KEY私钥文件
)

echo.
echo 5️⃣ 检查数据库连接字符串...
findstr /r /c:"mongodb://" *.* >nul 2>&1
if %errorlevel% equ 0 (
    echo ❌ 发现MongoDB连接字符串！
    findstr /r /c:"mongodb://" *.*
    set "found_issues=1"
)

findstr /r /c:"mysql://" *.* >nul 2>&1
if %errorlevel% equ 0 (
    echo ❌ 发现MySQL连接字符串！
    findstr /r /c:"mysql://" *.*
    set "found_issues=1"
)

findstr /r /c:"postgresql://" *.* >nul 2>&1
if %errorlevel% equ 0 (
    echo ❌ 发现PostgreSQL连接字符串！
    findstr /r /c:"postgresql://" *.*
    set "found_issues=1"
)

if %errorlevel% neq 0 (
    echo ✅ 未发现数据库连接字符串
)

echo.
echo 6️⃣ 检查邮箱和个人信息...
findstr /r /c:"@.*\.com" *.* | findstr /v /c:"example.com" | findstr /v /c:"users.noreply.github.com" >nul 2>&1
if %errorlevel% equ 0 (
    echo ⚠️  发现邮箱地址，请确认是否需要保护：
    findstr /r /c:"@.*\.com" *.* | findstr /v /c:"example.com" | findstr /v /c:"users.noreply.github.com"
) else (
    echo ✅ 未发现敏感邮箱地址
)

echo.
echo 7️⃣ 检查IP地址...
findstr /r /c:"[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}" *.* | findstr /v /c:"127.0.0.1" | findstr /v /c:"0.0.0.0" >nul 2>&1
if %errorlevel% equ 0 (
    echo ⚠️  发现IP地址，请确认是否需要保护：
    findstr /r /c:"[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}" *.* | findstr /v /c:"127.0.0.1" | findstr /v /c:"0.0.0.0"
) else (
    echo ✅ 未发现敏感IP地址
)

echo.
echo 8️⃣ 检查MT5账户信息...
findstr /r /c:"login.*[0-9]\{5,\}" *.* >nul 2>&1
if %errorlevel% equ 0 (
    echo ⚠️  发现可能的MT5账户信息：
    findstr /r /c:"login.*[0-9]\{5,\}" *.*
) else (
    echo ✅ 未发现MT5账户信息
)

echo.
echo ========================================
if %found_issues% equ 1 (
    echo ❌ 发现敏感信息！请在上传前处理
    echo.
    echo 🛠️  建议操作：
    echo 1. 删除或替换敏感信息
    echo 2. 使用环境变量存储敏感数据
    echo 3. 添加到.gitignore文件
    echo 4. 使用配置文件模板
) else (
    echo ✅ 安全检查通过！可以安全上传
)
echo ========================================

echo.
pause