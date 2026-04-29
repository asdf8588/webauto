@echo off
chcp 65001 >nul
echo ===============================================
echo   WebAuto 测试平台 - 一键启动
echo ===============================================
echo.

cd /d D:\pythonshiyan\webauto

:: 启动 Allure HTTP 服务
echo [1/3] 启动 Allure 报告服务 (端口 8080)...
start "Allure Report" cmd /k "python -m http.server 8080 --directory allure-report"

:: 等待一下
timeout /t 2 /nobreak >nul

:: 启动 Django 平台
echo [2/3] 启动 WebAuto 平台 (端口 8000)...
cd platform\backend
start "WebAuto Platform" cmd /k ".venv\Scripts\python.exe manage.py runserver 8000"

:: 等待一下
timeout /t 2 /nobreak >nul

:: 打开浏览器
echo [3/3] 打开浏览器...
start http://localhost:8000

echo.
echo ===============================================
echo   启动完成！
echo ===============================================
echo.
echo 访问地址:
echo   - WebAuto 平台: http://localhost:8000
echo   - Allure 报告:  http://localhost:8080
echo.
echo 按任意键退出此窗口(服务继续运行)...
pause >nul
