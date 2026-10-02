@echo off
echo Starting Paper Notion Agent...

:: Start Backend
start cmd /k "cd backend && title Backend Server && C:\Users\48427\.gemini\antigravity-ide\.venv\Scripts\python.exe main.py"

:: Wait 3 seconds
timeout /t 3 /nobreak >nul

:: Start Frontend
start cmd /k "cd frontend && title Frontend Server && npm run dev"

:: Wait 2 seconds
timeout /t 2 /nobreak >nul

:: Open Browser
start http://localhost:5173

echo Done! You can close this window now. The servers are running in the two new terminals.
exit
