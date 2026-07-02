@echo off
title CadGPT Launcher - Autonomous Mode
cls

echo ===================================================
echo   Starting CadGPT Platform Backend Connections...
echo ===================================================
echo.

:: 1. Variables de entorno para conectar con Qwen en LM Studio
set QWEN_MODEL=openai:qwen/qwen3.5-9b
set OPENAI_API_KEY=any-string
set OPENAI_BASE_URL=http://127.0.0.1:1234/v1

:: 2. Verificación rápida del servidor local (PARCHEADO CON -UseBasicParsing)
echo [System] Checking connection to LM Studio...
powershell -Command "try { $r = Invoke-WebRequest -Uri '%OPENAI_BASE_URL%/models' -TimeoutSec 2 -UseBasicParsing; echo '>>> Server Status: ONLINE' } catch { echo '>>> WARNING: LM Studio might be closed. Please open it and load the 9b model.' }"
echo.

:: 3. Lanzar el motor interactivo generativo
echo [System] Launching CadQuery pipeline...
echo.
python -m streamlit run app_visual.py

echo.
echo ===================================================
echo   Session closed. Press any key to exit.
echo ===================================================
pause > nul