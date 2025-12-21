# -*- mode: python ; coding: utf-8 -*-
"""
微信公众号爬虫 PyInstaller 打包配置
版本: 3.8.0
"""

import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules, collect_all

block_cipher = None

# UPX 压缩配置 - 如果存在则使用
UPX_DIR = r'D:\下载\upx-5.0.2-win64\upx-5.0.2-win64'

# 使用 collect_all 完整收集 qfluentwidgets（包括数据文件、二进制文件和隐藏导入）
qfluentwidgets_datas, qfluentwidgets_binaries, qfluentwidgets_hiddenimports = collect_all('qfluentwidgets')

# 收集 qframelesswindow（qfluentwidgets 的依赖）
qframelesswindow_datas, qframelesswindow_binaries, qframelesswindow_hiddenimports = collect_all('qframelesswindow')

# 收集 darkdetect（qfluentwidgets 的依赖）
darkdetect_datas, darkdetect_binaries, darkdetect_hiddenimports = collect_all('darkdetect')

# 收集 PyQt6 相关数据 (只收集必要的)
pyqt6_datas = collect_data_files('PyQt6')
pyqt6_webengine_datas = collect_data_files('PyQt6.QtWebEngineCore', include_py_files=False)

# 收集 PyQt6 多媒体模块数据
pyqt6_multimedia_datas = collect_data_files('PyQt6.QtMultimedia', include_py_files=False)

# 项目数据文件
datas = [
    ('config.json', '.'),
    ('gnivu-cfd69-001.ico', '.'),
    ('icons8-微信-64.png', '.'),
    # 音频文件
    ('mic', 'mic'),
]
datas += qfluentwidgets_datas
datas += qframelesswindow_datas
datas += darkdetect_datas
datas += pyqt6_datas
datas += pyqt6_webengine_datas
datas += pyqt6_multimedia_datas

# 二进制文件
binaries = []
binaries += qfluentwidgets_binaries
binaries += qframelesswindow_binaries
binaries += darkdetect_binaries

# 隐藏导入
hiddenimports = [
    # PyQt6 核心模块
    'PyQt6',
    'PyQt6.QtCore',
    'PyQt6.QtGui',
    'PyQt6.QtWidgets',
    'PyQt6.QtWebEngineWidgets',
    'PyQt6.QtWebEngineCore',
    'PyQt6.QtNetwork',
    'PyQt6.sip',
    # PyQt6 多媒体模块 (音频播放)
    'PyQt6.QtMultimedia',
    # qfluentwidgets
    'qfluentwidgets',
    # Selenium
    'selenium',
    'selenium.webdriver',
    'selenium.webdriver.chrome',
    'selenium.webdriver.chrome.service',
    'selenium.webdriver.chrome.options',
    'selenium.webdriver.common.by',
    'selenium.webdriver.support.ui',
    'selenium.webdriver.support.expected_conditions',
    # 网络请求
    'requests',
    'aiohttp',
    # 日志
    'loguru',
    # HTML 解析
    'bs4',
    'lxml',
    'lxml.etree',
    'lxml.html',
    # Markdown 转换
    'markdownify',
    # 进度条
    'tqdm',
    # 标准库
    'json',
    'asyncio',
    'concurrent.futures',
    # GUI 模块
    'gui',
    'gui.app',
    'gui.main_window',
    'gui.styles',
    'gui.widgets',
    'gui.workers',
    'gui.utils',
    'gui.history_manager',
    'gui.pages',
    'gui.pages.article_image_page',
    'gui.pages.content_search_page',
    'gui.pages.login_page',
    'gui.pages.results_page',
    'gui.pages.settings_page',
    'gui.pages.unified_scrape_page',
    'gui.pages.welcome_page',
    # Spider 模块
    'spider',
    'spider.log',
    'spider.log.utils',
    'spider.wechat',
    'spider.wechat.async_utils',
    'spider.wechat.cache_codec',
    'spider.wechat.login',
    'spider.wechat.run',
    'spider.wechat.scraper',
    'spider.wechat.utils',
]
hiddenimports += qfluentwidgets_hiddenimports
hiddenimports += qframelesswindow_hiddenimports
hiddenimports += darkdetect_hiddenimports

a = Analysis(
    ['run_gui.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 排除不需要的大型库
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'PIL',
        'Pillow',
        'tkinter',
        'unittest',
        'test',
        'tests',
        'setuptools',
        'pip',
        'wheel',
        'distutils',
        # 排除不需要的 PyQt6 模块
        'PyQt6.Qt3DCore',
        'PyQt6.Qt3DRender',
        'PyQt6.Qt3DInput',
        'PyQt6.Qt3DLogic',
        'PyQt6.Qt3DAnimation',
        'PyQt6.Qt3DExtras',
        'PyQt6.QtBluetooth',
        'PyQt6.QtDesigner',
        'PyQt6.QtHelp',
        'PyQt6.QtNfc',
        'PyQt6.QtPositioning',
        'PyQt6.QtRemoteObjects',
        'PyQt6.QtSensors',
        'PyQt6.QtSerialPort',
        'PyQt6.QtSql',
        'PyQt6.QtTest',
        'PyQt6.QtTextToSpeech',
        # 注意：不要排除 PyQt6.QtXml，qfluentwidgets 需要它
        # 排除调试相关
        'pdb',
        'doctest',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='WeChatSpider',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # 不显示控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='gnivu-cfd69-001.ico',  # 程序图标
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[
        'vcruntime140.dll',
        'ucrtbase.dll',
        'api-ms-win-*.dll',
        'Qt6WebEngine*.dll',
        'Qt6Quick*.dll',
    ],
    name='WeChatSpider',
)