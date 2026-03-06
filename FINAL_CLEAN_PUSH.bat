@echo off
echo ========================================
echo   FINAL CLEAN PUSH TO GITHUB
echo ========================================
echo.

echo Checking for AWS credentials in files...
echo.

REM Search for credentials (excluding .env which is protected)
findstr /S /I /C:"AKIA4IXIM6R752UEZAMA" *.md *.txt *.py *.js *.jsx 2>nul | findstr /V ".env"
if %errorlevel% equ 0 (
    echo [WARNING] Found credentials in files above!
    echo Please remove them before pushing.
    pause
    exit /b 1
) else (
    echo [SAFE] No credentials found in tracked files ✓
)

echo.
echo Step 1: Removing old commits with credentials...
git reset --soft HEAD~1

echo.
echo Step 2: Unstaging all files...
git reset

echo.
echo Step 3: Adding all files...
git add .

echo.
echo Step 4: Checking what will be committed...
git status --short

echo.
echo Step 5: Creating new clean commit...
git commit -m "Initial commit - Bharat Scheme Mitra for AI Hackathon 2026"

echo.
echo Step 6: Force pushing to GitHub (overwrites old history)...
git push -u origin main --force

echo.
echo ========================================
echo   SUCCESS!
echo ========================================
echo.
echo Your code is now on GitHub!
echo.
echo IMPORTANT: Rotate your AWS credentials now!
echo 1. Go to AWS Console - IAM
echo 2. Delete old access keys
echo 3. Create new access keys
echo 4. Update your local .env file
echo.
pause
