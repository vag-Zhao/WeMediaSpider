#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GUI 页面模块

本模块包含应用程序的所有功能页面，每个页面对应主窗口侧边栏的一个导航项。

页面列表:
    - WelcomePage: 欢迎页面，展示应用介绍和快速入门指南
    - LoginPage: 登录页面，提供微信扫码登录和凭证管理功能
    - UnifiedScrapePage: 公众号爬取页面，配置和执行批量爬取任务
    - ResultsPage: 结果查看页面，预览、筛选和导出爬取结果
    - SettingsPage: 设置页面，配置应用参数和爬取选项
    - ArticleImagePage: 图片提取页面，从文章中提取图片资源
    - ContentSearchPage: 内容搜索页面，支持正则表达式搜索文章内容

页面设计原则:
    1. 所有页面继承自 QWidget 或 ScrollArea
    2. 使用 qfluentwidgets 组件保持一致的 Fluent Design 风格
    3. 适配暗黑主题，使用微信绿作为强调色
    4. 支持屏幕自适应，在不同分辨率下都有良好体验
"""

from .welcome_page import WelcomePage
from .login_page import LoginPage
from .unified_scrape_page import UnifiedScrapePage
from .results_page import ResultsPage
from .settings_page import SettingsPage
from .article_image_page import ArticleImagePage
from .content_search_page import ContentSearchPage

__all__ = [
    'WelcomePage',
    'LoginPage',
    'UnifiedScrapePage',
    'ResultsPage',
    'SettingsPage',
    'ArticleImagePage',
    'ContentSearchPage'
]
