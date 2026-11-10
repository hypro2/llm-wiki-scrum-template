@echo off
chcp 65001 > nul
echo ============================================================
echo   🚀 Claude Code & Antigravity Sessions Sync Pipeline
echo ============================================================
echo.

where py >nul 2>nul
if %ERRORLEVEL% equ 0 (
    py "%~dp0scripts\sync_sessions.py" %*
) else (
    python "%~dp0scripts\sync_sessions.py" %*
)

echo.
echo ============================================================
echo   ✨ Pipeline Finished.
echo ============================================================
pause
