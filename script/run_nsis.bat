@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo Searching for NSIS...

:: Check common NSIS installation paths
set "NSIS_PATH="

if exist "C:\Program Files (x86)\NSIS\makensis.exe" (
    set "NSIS_PATH=C:\Program Files (x86)\NSIS\makensis.exe"
    goto :found
)

if exist "C:\Program Files\NSIS\makensis.exe" (
    set "NSIS_PATH=C:\Program Files\NSIS\makensis.exe"
    goto :found
)

:: Check winget installation location
for /f "tokens=*" %%i in ('where makensis 2^>nul') do (
    set "NSIS_PATH=%%i"
    goto :found
)

:: Search in common locations
for %%d in (C D E F G) do (
    if exist "%%d:\NSIS\makensis.exe" (
        set "NSIS_PATH=%%d:\NSIS\makensis.exe"
        goto :found
    )
)

:: Search in user's local app data
if exist "%LOCALAPPDATA%\Programs\NSIS\makensis.exe" (
    set "NSIS_PATH=%LOCALAPPDATA%\Programs\NSIS\makensis.exe"
    goto :found
)

:: Try registry
for /f "tokens=2*" %%a in ('reg query "HKLM\SOFTWARE\NSIS" /ve 2^>nul ^| findstr /i "REG_SZ"') do (
    if exist "%%b\makensis.exe" (
        set "NSIS_PATH=%%b\makensis.exe"
        goto :found
    )
)

for /f "tokens=2*" %%a in ('reg query "HKLM\SOFTWARE\WOW6432Node\NSIS" /ve 2^>nul ^| findstr /i "REG_SZ"') do (
    if exist "%%b\makensis.exe" (
        set "NSIS_PATH=%%b\makensis.exe"
        goto :found
    )
)

echo ERROR: NSIS not found!
echo Please install NSIS from https://nsis.sourceforge.io/
echo Or specify the path manually.
pause
exit /b 1

:found
echo Found NSIS at: %NSIS_PATH%
echo.

:: Change to project directory
cd /d "%~dp0.."
set "PROJECT_DIR=%CD%"
echo Project Directory: %PROJECT_DIR%
echo.

:: Run NSIS
echo Creating installer...
cd /d "%PROJECT_DIR%\script"
"%NSIS_PATH%" installer.nsi
if errorlevel 1 (
    echo ERROR: NSIS build failed
    pause
    exit /b 1
)

echo.
echo ============================================
echo   Installer created successfully!
echo ============================================
echo.
echo Output: %PROJECT_DIR%\dist\WeChatSpider_Setup_1.0.0.exe
echo.

:: Show file size
for %%f in ("%PROJECT_DIR%\dist\WeChatSpider_Setup_1.0.0.exe") do (
    echo File size: %%~zf bytes
)
echo.
pause