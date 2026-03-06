@echo off
echo ========================================
echo   REMOVING CREDENTIALS FROM GIT HISTORY
echo ========================================
echo.

echo This will remove the credentials from all commits...
echo.

REM Remove the problematic commit and start fresh
echo Step 1: Resetting to before the bad commit...
git reset --soft HEAD~1

echo.
echo Step 2: Unstaging all files...
git reset

echo.
echo Step 3: Re-adding files (credentials already removed)...
git add .

echo.
echo Step 4: Creating new commit without credentials...
git commit -m "Initial commit - Bharat Scheme Mitra (credentials removed)"

echo.
echo Step 5: Force pushing to GitHub...
git push -u origin main --force

echo.
echo ========================================
echo   DONE!
echo ========================================
echo.
pause
