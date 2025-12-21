#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信公众号爬虫 GUI 启动脚本

这是应用程序的入口文件，负责：
    1. 检测运行环境（开发环境 vs PyInstaller 打包环境）
    2. 设置 Python 模块搜索路径
    3. 检查必要的依赖库是否已安装
    4. 初始化 PyQt6 应用程序
    5. 配置 Fluent Design 主题
    6. 启动主窗口

使用方式：
    开发环境：python run_gui.py
    打包后：直接运行 WeChatSpider.exe

环境要求：
    - Python 3.8+
    - PyQt6
    - PyQt-Fluent-Widgets
    - 其他依赖见 requirements.txt

注意事项：
    - QApplication 的某些属性必须在实例化之前设置
    - QtWebEngine 需要 OpenGL 共享上下文
    - 高 DPI 显示器需要特殊处理
"""

import sys
import os


# ============================================================
# 环境检测
# ============================================================

def is_frozen():
    """
    检查是否在 PyInstaller 打包环境中运行
    
    PyInstaller 打包后会设置 sys.frozen 属性，
    并将资源文件解压到 sys._MEIPASS 临时目录。
    
    Returns:
        bool: 如果是打包环境返回 True
    """
    return getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')


# 根据运行环境设置基础路径
if is_frozen():
    # 打包环境：使用 PyInstaller 的临时解压目录
    base_path = sys._MEIPASS
else:
    # 开发环境：使用脚本所在目录，并添加到模块搜索路径
    base_path = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, base_path)


# ============================================================
# 依赖检查
# ============================================================

def check_basic_dependencies():
    """
    检查基础依赖库是否已安装
    
    在开发环境中检查必要的第三方库，打包环境中跳过检查
    （因为打包时已经包含了所有依赖）。
    
    Returns:
        bool: 所有依赖都已安装返回 True，否则返回 False
    """
    # 打包环境中跳过依赖检查
    if is_frozen():
        return True
    
    missing = []
    
    # 依赖列表：(模块名, pip包名)
    # 模块名用于 import 检查，pip包名用于安装提示
    deps = [
        ('PyQt6', 'PyQt6'),
        ('selenium', 'selenium'),
        ('requests', 'requests'),
        ('loguru', 'loguru'),
        ('bs4', 'beautifulsoup4'),
        ('markdownify', 'markdownify'),
        ('tqdm', 'tqdm'),
        ('lxml', 'lxml'),
    ]
    
    # 逐个检查依赖
    for module, package in deps:
        try:
            __import__(module)
        except ImportError:
            missing.append(package)
    
    # 输出缺失的依赖
    if missing:
        print("缺少以下依赖，请先安装:")
        print(f"  pip install {' '.join(missing)}")
        return False
    
    return True


# ============================================================
# 主函数
# ============================================================

def main():
    """
    应用程序主函数
    
    执行流程：
        1. 显示启动信息
        2. 检查依赖
        3. 配置 Qt 应用程序属性
        4. 创建 QApplication 实例
        5. 设置 Fluent Design 主题
        6. 创建并显示主窗口
        7. 进入事件循环
    """
    # 显示启动信息
    print("=" * 50)
    print("微信公众号爬虫 GUI 版本")
    print("=" * 50)
    print()
    
    # 检查依赖
    print("正在检查依赖...")
    if not check_basic_dependencies():
        sys.exit(1)
    print("依赖检查通过！")
    print()
    
    print("正在启动图形界面...")
    
    # 导入 Qt 模块（延迟导入，确保依赖检查通过后再导入）
    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtGui import QFont
    
    # ---- Qt 应用程序属性设置（必须在 QApplication 创建前） ----
    
    # 启用 OpenGL 共享上下文
    # QtWebEngine（用于内嵌浏览器）需要此设置才能正常工作
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts, True)
    
    # 高 DPI 缩放策略
    # PassThrough 模式让 Qt 使用系统的 DPI 缩放，避免界面模糊
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    # ---- 创建应用程序实例 ----
    
    app = QApplication(sys.argv)
    app.setApplicationName("微信公众号爬虫")
    app.setApplicationVersion("1.0")
    
    # 设置默认字体为微软雅黑，更适合中文显示
    app.setFont(QFont("Microsoft YaHei", 10))
    
    # ---- 配置 Fluent Design 主题 ----
    
    try:
        from qfluentwidgets import setTheme, Theme, setThemeColor
        
        # 使用暗黑主题
        setTheme(Theme.DARK)
        
        # 设置主题色为微信绿
        setThemeColor("#07C160")
        
    except ImportError as e:
        print(f"缺少 PyQt-Fluent-Widgets，请安装: pip install PyQt-Fluent-Widgets")
        print(f"错误详情: {e}")
        if is_frozen():
            # 打包环境中打印完整堆栈，便于调试
            import traceback
            traceback.print_exc()
        sys.exit(1)
    
    # ---- 创建并显示主窗口 ----
    
    from gui.main_window import MainWindow
    window = MainWindow()
    window.show()
    
    # 进入 Qt 事件循环，直到窗口关闭
    sys.exit(app.exec())


# ============================================================
# 程序入口
# ============================================================

if __name__ == "__main__":
    main()
