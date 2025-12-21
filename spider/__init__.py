#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信公众号爬虫包
===============

这个包提供了微信公众号文章爬取的完整解决方案，包括登录认证、
文章列表获取、内容解析等功能。设计上采用模块化架构，可以
独立使用各个组件，也可以组合使用实现复杂的爬取任务。

模块结构:
    - wechat: 核心爬虫模块，包含登录、爬取、解析等功能
    - log: 日志模块，提供统一的日志记录功能

导出的类:
    - WeChatSpiderLogin: 微信公众平台登录管理器
    - WeChatScraper: 单公众号爬虫类
    - BatchWeChatScraper: 批量爬取管理器

导出的函数:
    - setup_logger: 配置日志记录器
    - logger: 预配置的日志实例

使用示例:
    >>> from spider import WeChatSpiderLogin, WeChatScraper
    >>> login = WeChatSpiderLogin()
    >>> if login.login():
    ...     scraper = WeChatScraper(login.get_token(), login.get_headers())
    ...     articles = scraper.get_account_articles('公众号名称')
"""

from .wechat import WeChatSpiderLogin, WeChatScraper, BatchWeChatScraper
from .log import setup_logger, logger

__all__ = [
    'WeChatSpiderLogin',
    'WeChatScraper',
    'BatchWeChatScraper',
    'setup_logger',
    'logger'
]

__version__ = '3.8.0'
__author__ = 'WeMediaSpider Team'
