; NSIS Installer Script for WeChat Spider
; Encoding: UTF-8 with BOM
; Version: 3.8.0

!include "MUI2.nsh"
!include "FileFunc.nsh"

; Application Info
!define PRODUCT_NAME "WeChat Spider"
!define PRODUCT_NAME_CN "微信公众号爬虫"
!define PRODUCT_VERSION "3.8.0"
!define PRODUCT_PUBLISHER "WeChatSpider"
!define PRODUCT_WEB_SITE "https://github.com/WeChatSpider"
!define PRODUCT_DIR_REGKEY "Software\Microsoft\Windows\CurrentVersion\App Paths\WeChatSpider.exe"
!define PRODUCT_UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}"
!define PRODUCT_UNINST_ROOT_KEY "HKLM"
!define EXE_NAME "WeChatSpider.exe"
!define ICON_NAME "gnivu-cfd69-001.ico"

; Compression - Use LZMA with reasonable compression settings
SetCompressor /SOLID lzma
SetCompressorDictSize 32
SetDatablockOptimize on

; MUI Settings
!define MUI_ABORTWARNING
!define MUI_ICON "..\gnivu-cfd69-001.ico"
!define MUI_UNICON "..\gnivu-cfd69-001.ico"
!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_BITMAP "${NSISDIR}\Contrib\Graphics\Header\nsis.bmp"
!define MUI_WELCOMEFINISHPAGE_BITMAP "${NSISDIR}\Contrib\Graphics\Wizard\win.bmp"

; Welcome page
!insertmacro MUI_PAGE_WELCOME
; License page (optional)
; !insertmacro MUI_PAGE_LICENSE "..\LICENSE"
; Directory page
!insertmacro MUI_PAGE_DIRECTORY
; Instfiles page
!insertmacro MUI_PAGE_INSTFILES
; Finish page
!define MUI_FINISHPAGE_RUN "$INSTDIR\${EXE_NAME}"
!define MUI_FINISHPAGE_RUN_TEXT "运行 ${PRODUCT_NAME_CN}"
!define MUI_FINISHPAGE_SHOWREADME ""
!define MUI_FINISHPAGE_SHOWREADME_NOTCHECKED
!insertmacro MUI_PAGE_FINISH

; Uninstaller pages
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

; Language files - Chinese first as default
!insertmacro MUI_LANGUAGE "SimpChinese"
!insertmacro MUI_LANGUAGE "English"

; Installer attributes
Name "${PRODUCT_NAME_CN} ${PRODUCT_VERSION}"
OutFile "..\dist\WeChatSpider_Setup_${PRODUCT_VERSION}.exe"
InstallDir "$PROGRAMFILES\${PRODUCT_NAME}"
InstallDirRegKey HKLM "${PRODUCT_DIR_REGKEY}" ""
ShowInstDetails show
ShowUnInstDetails show
RequestExecutionLevel admin

; Version Info
VIProductVersion "3.8.0.0"
VIAddVersionKey /LANG=${LANG_SIMPCHINESE} "ProductName" "${PRODUCT_NAME_CN}"
VIAddVersionKey /LANG=${LANG_SIMPCHINESE} "CompanyName" "${PRODUCT_PUBLISHER}"
VIAddVersionKey /LANG=${LANG_SIMPCHINESE} "FileDescription" "${PRODUCT_NAME_CN} 安装程序"
VIAddVersionKey /LANG=${LANG_SIMPCHINESE} "FileVersion" "${PRODUCT_VERSION}"
VIAddVersionKey /LANG=${LANG_SIMPCHINESE} "ProductVersion" "${PRODUCT_VERSION}"
VIAddVersionKey /LANG=${LANG_SIMPCHINESE} "LegalCopyright" "Copyright (C) 2024-2025 ${PRODUCT_PUBLISHER}"

Section "MainSection" SEC01
    SetOutPath "$INSTDIR"
    SetOverwrite on
    
    ; Copy all files from PyInstaller output
    File /r "..\dist\WeChatSpider\*.*"
    
    ; Copy icon file separately for shortcuts
    File "..\${ICON_NAME}"
    
    ; Create shortcuts with icon - use the dedicated icon file
    CreateDirectory "$SMPROGRAMS\${PRODUCT_NAME_CN}"
    CreateShortCut "$SMPROGRAMS\${PRODUCT_NAME_CN}\${PRODUCT_NAME_CN}.lnk" "$INSTDIR\${EXE_NAME}" "" "$INSTDIR\${ICON_NAME}" 0
    CreateShortCut "$SMPROGRAMS\${PRODUCT_NAME_CN}\卸载 ${PRODUCT_NAME_CN}.lnk" "$INSTDIR\uninst.exe" "" "$INSTDIR\uninst.exe" 0
    CreateShortCut "$DESKTOP\${PRODUCT_NAME_CN}.lnk" "$INSTDIR\${EXE_NAME}" "" "$INSTDIR\${ICON_NAME}" 0
    
    ; Create user data directory in Documents (not in Program Files to avoid permission issues)
    ; The application will create this directory automatically when needed
    ; CreateDirectory "$DOCUMENTS\WeChatSpider"
    
    ; Create logs directory in INSTDIR (for application logs)
    CreateDirectory "$INSTDIR\logs"
SectionEnd

Section -AdditionalIcons
    WriteIniStr "$INSTDIR\${PRODUCT_NAME}.url" "InternetShortcut" "URL" "${PRODUCT_WEB_SITE}"
    CreateShortCut "$SMPROGRAMS\${PRODUCT_NAME_CN}\项目主页.lnk" "$INSTDIR\${PRODUCT_NAME}.url" "" "" 0
SectionEnd

Section -Post
    WriteUninstaller "$INSTDIR\uninst.exe"
    WriteRegStr HKLM "${PRODUCT_DIR_REGKEY}" "" "$INSTDIR\${EXE_NAME}"
    WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayName" "${PRODUCT_NAME_CN}"
    WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "UninstallString" "$INSTDIR\uninst.exe"
    WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayIcon" "$INSTDIR\${ICON_NAME}"
    WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayVersion" "${PRODUCT_VERSION}"
    WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "URLInfoAbout" "${PRODUCT_WEB_SITE}"
    WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "Publisher" "${PRODUCT_PUBLISHER}"
    WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "InstallLocation" "$INSTDIR"
    
    ; Calculate installed size
    ${GetSize} "$INSTDIR" "/S=0K" $0 $1 $2
    IntFmt $0 "0x%08X" $0
    WriteRegDWORD ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "EstimatedSize" "$0"
SectionEnd

Function un.onUninstSuccess
    HideWindow
    MessageBox MB_ICONINFORMATION|MB_OK "${PRODUCT_NAME_CN} 已成功卸载。"
FunctionEnd

Function un.onInit
    MessageBox MB_ICONQUESTION|MB_YESNO|MB_DEFBUTTON2 "确定要卸载 ${PRODUCT_NAME_CN} 吗？" IDYES +2
    Abort
FunctionEnd

Section Uninstall
    ; Remove shortcuts
    Delete "$SMPROGRAMS\${PRODUCT_NAME_CN}\卸载 ${PRODUCT_NAME_CN}.lnk"
    Delete "$SMPROGRAMS\${PRODUCT_NAME_CN}\项目主页.lnk"
    Delete "$SMPROGRAMS\${PRODUCT_NAME_CN}\${PRODUCT_NAME_CN}.lnk"
    Delete "$DESKTOP\${PRODUCT_NAME_CN}.lnk"
    RMDir "$SMPROGRAMS\${PRODUCT_NAME_CN}"
    
    ; Remove files and directories
    RMDir /r "$INSTDIR"
    
    ; Remove registry keys
    DeleteRegKey ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}"
    DeleteRegKey HKLM "${PRODUCT_DIR_REGKEY}"
    
    SetAutoClose true
SectionEnd