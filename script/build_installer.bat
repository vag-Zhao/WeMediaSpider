@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ============================================
echo   WeChat Spider Build Script with UPX
echo   Version 3.8.0
echo ============================================
echo.

:: Set working directory
cd /d "%~dp0.."
set "PROJECT_DIR=%CD%"
set "VERSION=3.8.0"
echo Project Directory: %PROJECT_DIR%
echo Version: %VERSION%
echo.

:: UPX Path - Try multiple locations
set "UPX_PATH="
if exist "D:\下载\upx-5.0.2-win64\upx-5.0.2-win64\upx.exe" (
    set "UPX_PATH=D:\下载\upx-5.0.2-win64\upx-5.0.2-win64\upx.exe"
) else if exist "%PROJECT_DIR%\tools\upx.exe" (
    set "UPX_PATH=%PROJECT_DIR%\tools\upx.exe"
) else (
    where upx >nul 2>&1
    if not errorlevel 1 (
        for /f "tokens=*" %%i in ('where upx') do set "UPX_PATH=%%i"
    )
)

:: NSIS Path (common installation locations)
set "NSIS_PATH="
if exist "C:\Program Files (x86)\NSIS\makensis.exe" (
    set "NSIS_PATH=C:\Program Files (x86)\NSIS\makensis.exe"
) else if exist "C:\Program Files\NSIS\makensis.exe" (
    set "NSIS_PATH=C:\Program Files\NSIS\makensis.exe"
)

:: Check UPX
echo [0/8] Checking UPX...
if defined UPX_PATH (
    if exist "%UPX_PATH%" (
        echo UPX found at: %UPX_PATH%
    ) else (
        echo WARNING: UPX not found at %UPX_PATH%
        echo Will skip UPX compression step.
        set "UPX_PATH="
    )
) else (
    echo WARNING: UPX not found in any location.
    echo Will skip UPX compression step.
    echo To enable UPX compression, download from: https://github.com/upx/upx/releases
)
echo.

:: Check Python
echo [1/8] Checking Python environment...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found in PATH
    echo Please install Python and add to PATH
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('python --version 2^>^&1') do set PYTHON_VER=%%i
echo %PYTHON_VER% found.
echo.

:: Install dependencies
echo [2/8] Installing/Checking dependencies...
pip install pyinstaller --quiet --upgrade
if errorlevel 1 (
    echo ERROR: Failed to install PyInstaller
    pause
    exit /b 1
)
echo PyInstaller ready.
echo.

:: Clean previous build
echo [3/8] Cleaning previous build...
if exist "dist" (
    echo Removing dist folder...
    rmdir /s /q "dist"
)
if exist "build" (
    echo Removing build folder...
    rmdir /s /q "build"
)
echo Clean completed.
echo.

:: Run PyInstaller with UPX directory
echo [4/8] Running PyInstaller...
echo This may take several minutes...
echo.
if defined UPX_PATH (
    for %%i in ("%UPX_PATH%") do set "UPX_DIR=%%~dpi"
    pyinstaller --clean --noconfirm --upx-dir "!UPX_DIR!" WeChatSpider.spec
) else (
    pyinstaller --clean --noconfirm WeChatSpider.spec
)
if errorlevel 1 (
    echo ERROR: PyInstaller build failed
    pause
    exit /b 1
)
echo.
echo PyInstaller build completed.
echo.

:: Additional UPX Compression for files that PyInstaller might have missed
echo [5/8] Additional UPX compression...
if not defined UPX_PATH (
    echo Skipping UPX compression - UPX not found.
    goto :skip_upx
)

echo Compressing additional executable files...
echo.

:: Compress main exe if not already compressed
if exist "dist\WeChatSpider\WeChatSpider.exe" (
    echo Checking WeChatSpider.exe...
    "%UPX_PATH%" -t "dist\WeChatSpider\WeChatSpider.exe" >nul 2>&1
    if errorlevel 1 (
        echo Compressing WeChatSpider.exe...
        "%UPX_PATH%" --best --lzma "dist\WeChatSpider\WeChatSpider.exe" 2>nul
    ) else (
        echo WeChatSpider.exe already compressed.
    )
    echo.
)

:: Compress DLL files (skip some that don't compress well or cause issues)
echo Compressing DLL files...
set "COMPRESS_COUNT=0"
set "SKIP_COUNT=0"
for /r "dist\WeChatSpider" %%f in (*.dll) do (
    call :compress_dll "%%f" "%%~nxf"
)
echo Compressed !COMPRESS_COUNT! DLL files, skipped !SKIP_COUNT! files.

:: Compress PYD files
echo.
echo Compressing PYD files...
set "PYD_COUNT=0"
for /r "dist\WeChatSpider" %%f in (*.pyd) do (
    "%UPX_PATH%" -t "%%f" >nul 2>&1
    if errorlevel 1 (
        "%UPX_PATH%" --best --lzma "%%f" >nul 2>&1
        if not errorlevel 1 (
            set /a PYD_COUNT+=1
        )
    )
)
echo Compressed !PYD_COUNT! PYD files.

echo.
echo UPX compression completed.
goto :after_upx

:compress_dll
set "FILEPATH=%~1"
set "FILENAME=%~2"
:: Skip Qt WebEngine, Qt Quick, and some system DLLs that may cause issues
echo %FILENAME% | findstr /i "Qt6WebEngine Qt6Quick vcruntime ucrtbase api-ms-win msvcp python3" >nul 2>&1
if not errorlevel 1 (
    set /a SKIP_COUNT+=1
    goto :eof
)
"%UPX_PATH%" -t "%FILEPATH%" >nul 2>&1
if errorlevel 1 (
    "%UPX_PATH%" --best --lzma "%FILEPATH%" >nul 2>&1
    if not errorlevel 1 (
        set /a COMPRESS_COUNT+=1
    )
)
goto :eof

:skip_upx
:after_upx
echo.

:: Copy additional files to dist folder
echo [6/8] Copying additional files...
if exist "%PROJECT_DIR%\gnivu-cfd69-001.ico" (
    copy /y "%PROJECT_DIR%\gnivu-cfd69-001.ico" "%PROJECT_DIR%\dist\WeChatSpider\" >nul
    echo Icon file copied to dist folder.
) else (
    echo WARNING: Icon file not found!
)

:: Copy mic folder if not already included
if not exist "%PROJECT_DIR%\mic" (
    echo WARNING: Audio files folder - mic - not found!
    goto :after_mic_copy
)
if exist "%PROJECT_DIR%\dist\WeChatSpider\mic" (
    echo Audio files already in dist folder.
) else (
    xcopy /y /i /e "%PROJECT_DIR%\mic" "%PROJECT_DIR%\dist\WeChatSpider\mic\" >nul
    echo Audio files copied to dist folder.
)
:after_mic_copy
echo.

:: Remove unnecessary files to reduce size
echo [7/8] Cleaning up unnecessary files...
set "CLEANUP_COUNT=0"

:: Remove test files
for /r "%PROJECT_DIR%\dist\WeChatSpider" %%f in (*test*.py *_test.py test_*.py) do (
    del /q "%%f" 2>nul
    if not errorlevel 1 set /a CLEANUP_COUNT+=1
)

:: Remove __pycache__ directories
for /d /r "%PROJECT_DIR%\dist\WeChatSpider" %%d in (__pycache__) do (
    rmdir /s /q "%%d" 2>nul
    if not errorlevel 1 set /a CLEANUP_COUNT+=1
)

:: Remove .pyc files (if any loose ones)
for /r "%PROJECT_DIR%\dist\WeChatSpider" %%f in (*.pyc) do (
    del /q "%%f" 2>nul
    if not errorlevel 1 set /a CLEANUP_COUNT+=1
)

echo Cleaned up !CLEANUP_COUNT! unnecessary files/folders.
echo.

:: Check NSIS and create installer
echo [8/8] Creating installer with NSIS...
set "NSIS_FOUND=0"

:: Try to find NSIS in PATH first
where makensis >nul 2>&1
if not errorlevel 1 (
    set "NSIS_FOUND=1"
    set "NSIS_CMD=makensis"
)

:: If not in PATH, try common installation locations
if "%NSIS_FOUND%"=="0" (
    if defined NSIS_PATH (
        if exist "%NSIS_PATH%" (
            set "NSIS_FOUND=1"
            set "NSIS_CMD=%NSIS_PATH%"
        )
    )
)

if "%NSIS_FOUND%"=="0" (
    echo WARNING: NSIS not found!
    echo Please install NSIS from https://nsis.sourceforge.io/
    echo Or add NSIS to PATH
    echo.
    echo PyInstaller output is available at: %PROJECT_DIR%\dist\WeChatSpider
    echo You can manually create installer using script\installer.nsi
    echo.
    goto :show_size
)

:: Run NSIS
echo Using NSIS: %NSIS_CMD%
cd /d "%PROJECT_DIR%\script"
"%NSIS_CMD%" installer.nsi
if errorlevel 1 (
    echo ERROR: NSIS build failed
    echo Please check the installer.nsi script for errors.
    pause
    exit /b 1
)
echo NSIS installer created successfully.
echo.

:show_size
:: Show file sizes
cd /d "%PROJECT_DIR%"
echo ============================================
echo   Build completed successfully!
echo ============================================
echo.
echo Output files:
echo   - Portable: %PROJECT_DIR%\dist\WeChatSpider\

:: Calculate folder size
set "FOLDER_SIZE=0"
set "FILE_COUNT=0"
for /f "tokens=1,3" %%a in ('dir /s "%PROJECT_DIR%\dist\WeChatSpider" 2^>nul ^| findstr /c:"File(s)"') do (
    set "FILE_COUNT=%%a"
    set "FOLDER_SIZE=%%b"
)
echo   - Portable Size: %FOLDER_SIZE% bytes (%FILE_COUNT% files)

if exist "%PROJECT_DIR%\dist\WeChatSpider_Setup_%VERSION%.exe" (
    for %%f in ("%PROJECT_DIR%\dist\WeChatSpider_Setup_%VERSION%.exe") do (
        set "INSTALLER_SIZE=%%~zf"
        set /a "INSTALLER_MB=!INSTALLER_SIZE! / 1048576"
    )
    echo   - Installer: %PROJECT_DIR%\dist\WeChatSpider_Setup_%VERSION%.exe
    echo   - Installer Size: !INSTALLER_SIZE! bytes (~!INSTALLER_MB! MB)
)
echo.
echo ============================================
echo   Installation package ready!
echo   Version: %VERSION%
echo ============================================
echo.
echo Next steps:
echo   1. Test the portable version: dist\WeChatSpider\WeChatSpider.exe
echo   2. Test the installer: dist\WeChatSpider_Setup_%VERSION%.exe
echo.
pause