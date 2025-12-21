@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ============================================
echo   WeChat Spider Build Script
echo ============================================
echo.

:: Set working directory
cd /d "%~dp0.."
set "PROJECT_DIR=%CD%"
echo Project Directory: %PROJECT_DIR%
echo.

:: Check Python
echo [1/5] Checking Python environment...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found in PATH
    echo Please install Python and add to PATH
    pause
    exit /b 1
)
echo Python found.
echo.

:: Install dependencies
echo [2/5] Installing dependencies...
pip install pyinstaller --quiet
if errorlevel 1 (
    echo ERROR: Failed to install PyInstaller
    pause
    exit /b 1
)
echo PyInstaller installed.
echo.

:: Clean previous build
echo [3/5] Cleaning previous build...
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"
echo Clean completed.
echo.

:: Run PyInstaller
echo [4/5] Running PyInstaller...
echo This may take several minutes...
pyinstaller --clean --noconfirm WeChatSpider.spec
if errorlevel 1 (
    echo ERROR: PyInstaller build failed
    pause
    exit /b 1
)
echo PyInstaller build completed.
echo.

:: Copy icon file to output directory
echo Copying icon file...
copy "%PROJECT_DIR%\gnivu-cfd69-001.ico" "%PROJECT_DIR%\dist\WeChatSpider\" >nul
echo Icon file copied.
echo.

:: Check NSIS
echo [5/5] Creating installer with NSIS...
where makensis >nul 2>&1
if errorlevel 1 (
    echo WARNING: NSIS not found in PATH
    echo Please install NSIS from https://nsis.sourceforge.io/
    echo Or add NSIS to PATH
    echo.
    echo PyInstaller output is available at: %PROJECT_DIR%\dist\WeChatSpider
    echo You can manually create installer using script\installer.nsi
    pause
    exit /b 0
)

:: Run NSIS
cd /d "%PROJECT_DIR%\script"
makensis installer.nsi
if errorlevel 1 (
    echo ERROR: NSIS build failed
    pause
    exit /b 1
)
echo NSIS installer created.
echo.

echo ============================================
echo   Build completed successfully!
echo ============================================
echo.
echo Output files:
echo   - Portable: %PROJECT_DIR%\dist\WeChatSpider\
echo   - Installer: %PROJECT_DIR%\dist\WeChatSpider_Setup_1.0.0.exe
echo.
pause