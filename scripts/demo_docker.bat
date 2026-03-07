@echo off
REM ============================================================================
REM FWMS Demo Preparation — Docker Exec Version
REM ============================================================================
REM Usage: scripts\demo_docker.bat
REM
REM Runs SQL seed inside Docker container, then calls allocation API.
REM ============================================================================

echo.
echo ============================================================
echo   FWMS DEMO PREPARATION (Docker)
echo ============================================================
echo.

REM Step 1-4: Run SQL demo seed
echo [1/2] Running SQL demo seed inside Docker...
docker cp "%~dp0demo_seed.sql" faculty_selection_db:/tmp/demo_seed.sql
docker exec faculty_selection_db psql -U postgres -d faculty_selection -f /tmp/demo_seed.sql

if %ERRORLEVEL% NEQ 0 (
    echo   X SQL seed failed!
    exit /b 1
)
echo   Done.
echo.

REM Step 5: Run allocation via API
echo [2/2] Running allocation engine via API...
curl -s -X POST http://localhost:8000/api/auth/dev-login > %TEMP%\fwms_token.json
for /f "tokens=2 delims=:," %%a in ('findstr "token" %TEMP%\fwms_token.json') do set TOKEN=%%~a
set TOKEN=%TOKEN: =%
set TOKEN=%TOKEN:"=%

curl -s -X POST http://localhost:8000/api/allocation/run -H "Authorization: Bearer %TOKEN%" -H "Content-Type: application/json"

echo.
echo.
echo ============================================================
echo   DEMO READY
echo ============================================================
echo   Open: http://localhost:5173/dashboard
echo ============================================================
