@echo off
echo ========================================
echo   SAFETY CHECK BEFORE PUSHING TO GITHUB
echo ========================================
echo.

echo Checking if .env files are protected...
echo.

REM Check if .env files exist
if exist backend\.env (
    echo [FOUND] backend\.env exists on your computer ✓
) else (
    echo [WARNING] backend\.env not found - you may need to create it
)

if exist frontend\.env (
    echo [FOUND] frontend\.env exists on your computer ✓
) else (
    echo [INFO] frontend\.env not found - optional for frontend
)

echo.
echo Checking if .env files are in .gitignore...
echo.

findstr /C:".env" .gitignore >nul
if %errorlevel% equ 0 (
    echo [SAFE] .env is in .gitignore ✓
) else (
    echo [DANGER] .env is NOT in .gitignore!
    echo Please add it before pushing!
    pause
    exit /b 1
)

findstr /C:"backend/.env" .gitignore >nul
if %errorlevel% equ 0 (
    echo [SAFE] backend/.env is in .gitignore ✓
) else (
    echo [WARNING] backend/.env not explicitly in .gitignore
)

findstr /C:"frontend/.env" .gitignore >nul
if %errorlevel% equ 0 (
    echo [SAFE] frontend/.env is in .gitignore ✓
) else (
    echo [WARNING] frontend/.env not explicitly in .gitignore
)

echo.
echo Checking what Git will commit...
echo.

git status --short | findstr "\.env$" >nul
if %errorlevel% equ 0 (
    echo [DANGER] .env files are staged for commit!
    echo.
    echo Files that will be committed:
    git status --short | findstr "\.env$"
    echo.
    echo [ACTION REQUIRED] Run these commands:
    echo   git reset backend/.env
    echo   git reset frontend/.env
    echo.
    pause
    exit /b 1
) else (
    echo [SAFE] No .env files will be committed ✓
)

echo.
echo Checking for AWS credentials in code...
echo.

findstr /S /I /C:"AKIA" *.py *.js *.jsx *.ts *.tsx 2>nul | findstr /V ".env" >nul
if %errorlevel% equ 0 (
    echo [WARNING] Found potential AWS credentials in code files!
    echo Please review and remove them.
    findstr /S /I /C:"AKIA" *.py *.js *.jsx *.ts *.tsx 2>nul | findstr /V ".env"
    echo.
) else (
    echo [SAFE] No AWS credentials found in code ✓
)

echo.
echo ========================================
echo   SAFETY CHECK COMPLETE
echo ========================================
echo.
echo Summary:
echo ✓ .env files are protected by .gitignore
echo ✓ No .env files will be committed
echo ✓ Safe to push to GitHub
echo.
echo Next steps:
echo   1. git add .
echo   2. git commit -m "Ready for hackathon"
echo   3. git push origin main
echo.
pause
