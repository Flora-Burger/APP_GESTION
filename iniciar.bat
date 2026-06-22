@echo off
chcp 65001 >nul
setlocal EnableExtensions

REM Ir al directorio del proyecto (donde esta este .bat)
cd /d "%~dp0"

set "PYTHON=%~dp0VFLORA\Scripts\python.exe"
set "UVICORN=%~dp0VFLORA\Scripts\uvicorn.exe"
set "ALEMBIC=%~dp0VFLORA\Scripts\alembic.exe"
set "HOST=127.0.0.1"
set "PORT=8000"

echo ============================================
echo   FLORA - Gestion de recursos
echo ============================================
echo.

if not exist "%PYTHON%" (
    echo [ERROR] No se encuentra el entorno virtual VFLORA.
    echo.
    echo Ejecute primero la instalacion:
    echo   powershell -ExecutionPolicy Bypass -File scripts\setup.ps1
    echo.
    pause
    exit /b 1
)

if not exist ".env" (
    echo [INFO] Creando archivo .env desde .env.example...
    copy /Y ".env.example" ".env" >nul
)

if not exist "data" (
    echo [INFO] Creando carpeta data...
    mkdir "data"
)

echo [INFO] Aplicando migraciones de base de datos...
"%ALEMBIC%" upgrade head
if errorlevel 1 (
    echo [ERROR] Fallo al aplicar migraciones.
    pause
    exit /b 1
)

echo.
echo [INFO] Liberando puerto %PORT% si esta en uso...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\liberar_puerto.ps1" -Puerto %PORT%
echo.
echo [INFO] Iniciando servidor en http://%HOST%:%PORT%
echo [INFO] Documentacion API: http://%HOST%:%PORT%/docs
echo [INFO] Pulse Ctrl+C para detener el servidor.
echo.

REM Abrir el navegador tras un breve retraso
start "" cmd /c "timeout /t 2 /nobreak >nul && start http://%HOST%:%PORT%/"

"%UVICORN%" backend.app.main:app --reload --host %HOST% --port %PORT%

pause
