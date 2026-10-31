@echo off
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Virtual environment not found. Create it first with:
    echo   python -m venv .venv
    echo   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
    pause
    exit /b 1
)

echo Starting Academic Desk...
echo Browser will open at http://127.0.0.1:8501
echo Close this window to stop the app.
echo.

start "" /min cmd /c "timeout /t 3 /nobreak >nul & start http://127.0.0.1:8501"

".\.venv\Scripts\python.exe" -m streamlit run app.py --server.headless true --server.address 127.0.0.1 --server.port 8501

pause
