@echo off
echo ========================================
echo GLAMORA - GitHub Push Script
echo ========================================
echo.

REM Check if Git is installed
git --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Git is not installed!
    echo.
    echo Please install Git first:
    echo 1. Download from: https://git-scm.com/download/win
    echo 2. Install Git
    echo 3. Restart this terminal/PowerShell
    echo 4. Run this script again
    pause
    exit /b 1
)

echo Git is installed!
echo.

REM Check if already initialized
if exist .git (
    echo Git repository already initialized.
) else (
    echo Initializing Git repository...
    git init
    echo.
)

echo Checking Git status...
git status
echo.

echo ========================================
echo IMPORTANT: Review the files above
echo Make sure .env file is NOT listed
echo ========================================
echo.
pause

echo.
echo Adding all files to Git...
git add .
echo.

echo Creating initial commit...
git commit -m "Initial commit: GLAMORA Django application"
echo.

echo ========================================
echo Your GitHub Repository:
echo https://github.com/CodeBase-05/GLAMORA
echo ========================================
echo.
echo Would you like to connect and push now? (Y/N)
set /p setup_remote="Enter Y or N: "

if /i "%setup_remote%"=="Y" (
    echo.
    echo Connecting to GitHub repository...
    git remote add origin https://github.com/CodeBase-05/GLAMORA.git
    if errorlevel 1 (
        echo.
        echo Remote might already exist. Updating URL...
        git remote set-url origin https://github.com/CodeBase-05/GLAMORA.git
    )
    echo.
    echo Setting branch to main...
    git branch -M main
    echo.
    echo Pushing to GitHub...
    echo Note: You may be prompted for GitHub credentials.
    echo Username: CodeBase-05
    echo Password: Use Personal Access Token (not GitHub password)
    echo.
    git push -u origin main
    if errorlevel 1 (
        echo.
        echo ========================================
        echo Push failed. Common issues:
        echo ========================================
        echo 1. Authentication failed - Use Personal Access Token
        echo    Get token from: GitHub Settings ^> Developer settings ^> Personal access tokens
        echo 2. Repository not found - Check repository exists
        echo 3. Network issues - Check internet connection
        echo.
        echo You can try pushing manually later with:
        echo git push -u origin main
    ) else (
        echo.
        echo ========================================
        echo SUCCESS! Your code is now on GitHub!
        echo ========================================
        echo.
        echo View your repository at:
        echo https://github.com/CodeBase-05/GLAMORA
    )
) else (
    echo.
    echo To push later, run these commands:
    echo git remote add origin https://github.com/CodeBase-05/GLAMORA.git
    echo git branch -M main
    echo git push -u origin main
)

echo.
pause

