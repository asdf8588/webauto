@echo off
chcp 65001 >nul
echo ========================================
echo   WebAuto Test Platform - 一键启动
echo ========================================
echo.

REM 设置项目根目录
set "ROOT_DIR=%~dp0.."
set "BACKEND_DIR=%ROOT_DIR%\platform\backend"
set "FRONTEND_DIR=%ROOT_DIR%\platform\frontend"

echo [1/5] 检查 Python 环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] 未找到 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)

REM 设置 Node.js 路径
set "NODE_DIR=C:\nodejs\node-v22.14.0-win-x64"
set "PATH=%NODE_DIR%;%PATH%"

echo [2/5] 检查 Node.js 环境...
node --version >nul 2>&1
if errorlevel 1 (
    echo [WARNING] 未找到 Node.js，前端将无法启动
)

echo [3/5] 安装 Python 依赖...
pushd "%BACKEND_DIR%"
if not exist ".venv" (
    echo     创建虚拟环境...
    python -m venv .venv
)
call .venv\Scripts\activate.bat
pip install -q -r requirements.txt
if errorlevel 1 (
    echo [ERROR] pip install 失败
    pause
    exit /b 1
)
echo     ✅ Python 依赖已就绪

echo [4/5] 数据库迁移...
python manage.py migrate --run-syncdb 2>nul || python manage.py migrate
echo     ✅ 数据库已准备就绪

echo [5/5] 启动服务...
echo.
echo ══════════════════════════════════
echo   后端服务: http://localhost:8000
echo   前端服务: http://localhost:5173  
echo   管理后台: http://localhost:8000/admin
echo ══════════════════════════════════
echo.
echo 按 Ctrl+C 停止服务
echo.

REM 启动后端（后台）
start "WebAuto Backend" cmd /c "call .venv\Scripts\activate.bat && python manage.py runserver 0.0.0.0:8000"
timeout /t 3 /nobreak >nul

REM 启动前端（后台）
if exist "%FRONTEND_DIR%\package.json" (
    pushd "%FRONTEND_DIR%"
    if not exist "node_modules" (
        echo 安装前端依赖...
        call npm install
    )
    start "WebAuto Frontend" cmd /c "npm run dev"
    popd
    timeout /t 3 /nobreak >nul
)

echo.
echo ✅ 服务已启动！
echo 正在打开浏览器...
timeout /t 2 /nobreak >nul
start http://localhost:5173

REM 保持窗口
pause
