@echo off
echo ========================================
echo   REMOVING CREDENTIALS AND PUSHING
echo ========================================
echo.

echo Step 1: Adding fixed files...
git add GITHUB_PUSH_GUIDE.md
git add PUSH_TO_GITHUB_NOW.md

echo.
echo Step 2: Committing changes...
git commit -m "Remove AWS credentials from documentation files"

echo.
echo Step 3: Pushing to GitHub...
git push -u origin main

echo.
echo ========================================
echo   DONE!
echo ========================================
echo.
echo Your code is now on GitHub without credentials!
echo.
pause
