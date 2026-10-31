# Start Academic Desk and open the browser.
Set-Location -Path $PSScriptRoot

$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    Write-Host "Virtual environment not found. Create it first with:"
    Write-Host "  python -m venv .venv"
    Write-Host "  .\.venv\Scripts\python.exe -m pip install -r requirements.txt"
    exit 1
}

Write-Host "Starting Academic Desk..."
Write-Host "Browser will open at http://127.0.0.1:8501"
Write-Host "Press Ctrl+C to stop the app."
Write-Host ""

Start-Job -ScriptBlock {
    Start-Sleep -Seconds 3
    Start-Process "http://127.0.0.1:8501"
} | Out-Null

& $python -m streamlit run app.py `
    --server.headless true `
    --server.address 127.0.0.1 `
    --server.port 8501
