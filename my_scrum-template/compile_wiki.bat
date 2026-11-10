@echo off
chcp 65001 > nul
echo ==========================================
echo       Compiling LLM Wiki (Obsidian)
echo ==========================================

set BUILD_PY=""
if exist "%~dp0..\Obsidian-Vault-Template\wiki\build.py" (
    set BUILD_PY="%~dp0..\Obsidian-Vault-Template\wiki\build.py"
) else if exist "%~dp0..\Obsidian-Vault\wiki\build.py" (
    set BUILD_PY="%~dp0..\Obsidian-Vault\wiki\build.py"
) else if exist "%USERPROFILE%\Documents\Obsidian Vault\wiki\build.py" (
    set BUILD_PY="%USERPROFILE%\Documents\Obsidian Vault\wiki\build.py"
)

if %BUILD_PY%=="" (
    echo [ERROR] wiki\build.py not found in adjacent or default Obsidian Vault directories.
    exit /b 1
)

where py >nul 2>nul
if %ERRORLEVEL% equ 0 (
    py %BUILD_PY%
) else (
    python %BUILD_PY%
)

echo.
echo Done.
