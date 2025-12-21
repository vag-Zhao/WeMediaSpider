#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信公众号爬虫核心模块
====================

这是爬虫的核心实现模块，封装了与微信公众平台交互的所有逻辑。
模块设计为无 GUI 依赖，可以作为独立库集成到其他项目中。

功能概述:
    登录认证 - 通过 Selenium 模拟扫码登录，获取访问凭证
    公众号搜索 - 根据名称搜索公众号并获取唯一标识
    文章爬取 - 支持分页获取历史文章列表
    内容解析 - 提取文章正文、图片等内容并转为 Markdown
    批量处理 - 支持多公众号并发爬取，提高效率

模块组成:
    login.py - 登录管理，处理认证和会话维护
    scraper.py - 爬虫实现，包含同步和异步两种模式
    utils.py - 工具函数，HTTP 请求、内容解析等
    async_utils.py - 异步工具，基于 aiohttp 的高性能实现
    cache_codec.py - 缓存编解码，用于登录凭证的分享和导入

技术栈:
    - Selenium: 浏览器自动化，处理扫码登录
    - Requests: 同步 HTTP 请求
    - aiohttp: 异步 HTTP 请求，提升并发性能
    - BeautifulSoup + lxml: HTML 解析
    - markdownify: HTML 转 Markdown

使用示例:
    # 基础用法
    from spider.wechat import WeChatSpiderLogin, WeChatScraper
    
    login = WeChatSpiderLogin()
    login.login()  # 会打开浏览器等待扫码
    
    scraper = WeChatScraper(login.get_token(), login.get_headers())
    articles = scraper.get_account_articles('人民日报', max_pages=5)
    
    # 批量爬取
    from spider.wechat import BatchWeChatScraper
    
    batch = BatchWeChatScraper()
    config = {
        'accounts': ['人民日报', '新华社'],
        'start_date': '2024-01-01',
        'end_date': '2024-01-31',
        'token': login.get_token(),
        'headers': login.get_headers()
    }
    all_articles = batch.start_batch_scrape(config)
"""

__version__ = "3.8.0"
__author__ = "WeMediaSpider Team"

from .login import WeChatSpiderLogin
from .scraper import WeChatScraper, BatchWeChatScraper
from .utils import get_timestamp, format_time

__all__ = [
    'WeChatSpiderLogin',
    'WeChatScraper',
    'BatchWeChatScraper',
    'get_timestamp',
    'format_time'
]