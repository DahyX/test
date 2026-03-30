@echo off
cd /d "C:\Users\DELL\OneDrive\Desktop\Test"
echo ============================================
echo   JARVIS V3 — Starting
echo ============================================

REM Show token file location if it exists
if exist jarvis_token.txt (
    echo API Token file: %cd%\jarvis_token.txt
)

"C:\Users\DELL\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.8_qbz5n2kfra8p0\python.exe" "C:\Users\DELL\OneDrive\Desktop\Test\jarvis.py"
pause
