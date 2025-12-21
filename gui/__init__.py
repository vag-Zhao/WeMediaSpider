#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
微信公众号爬虫 GUI 模块

本模块提供基于 PyQt6 和 qfluentwidgets 的图形用户界面，采用 Fluent Design 设计风格。
界面整体使用微信风格的暗黑主题配色，主色调为微信绿 (#07C160)。

模块结构:
    - app.py: 应用程序入口，负责初始化 QApplication 和主题设置
    - main_window.py: 主窗口实现，基于 FluentWindow 的导航式布局
    - pages/: 各功能页面的实现
        - welcome_page.py: 欢迎页面
        - login_page.py: 微信登录页面
        - unified_scrape_page.py: 公众号爬取页面
        - results_page.py: 结果查看页面
        - article_image_page.py: 图片提取页面
        - content_search_page.py: 内容搜索页面
        - settings_page.py: 设置页面
    - widgets.py: 自定义控件（进度条、卡片、历史标签等）
    - workers.py: 后台工作线程（同步/异步爬取）
    - styles.py: 全局样式定义
    - utils.py: 工具函数（路径处理、音频播放等）
    - history_manager.py: 公众号历史记录管理

使用示例:
    >>> from gui import run_app
    >>> run_app()  # 启动 GUI 应用

技术栈:
    - PyQt6: Qt6 的 Python 绑定
    - qfluentwidgets: Fluent Design 风格的 Qt 组件库
    - QMediaPlayer: 音频播放支持

作者: WeChatSpider Team
版本: 1.0
"""

__version__ = "1.0"

from .app import run_app

__all__ = ['run_app']
