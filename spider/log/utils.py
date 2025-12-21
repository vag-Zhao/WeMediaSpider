#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志工具模块
============

基于 loguru 实现的日志系统，提供灵活的日志配置和输出功能。
自动适配开发环境和打包环境，解决 PyInstaller 打包后的日志问题。

特性:
    - 自动检测运行环境（开发/打包）
    - 跨平台用户数据目录支持
    - 日志文件自动轮转（按大小）
    - 日志自动清理（按时间）
    - 彩色控制台输出
"""

import os
import sys
from loguru import logger


def get_app_dir():
    """
    获取应用程序所在目录
    
    根据运行环境返回不同的路径：
    - 打包环境: 返回可执行文件所在目录
    - 开发环境: 返回项目根目录
    
    Returns:
        str: 应用程序目录的绝对路径
    
    Note:
        PyInstaller 打包后 sys.frozen 会被设置为 True，
        此时 sys.executable 指向打包后的 exe 文件
    """
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        # 开发环境：向上两级到项目根目录
        return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def get_user_data_dir():
    """
    获取用户数据存储目录
    
    返回适合当前操作系统的用户数据目录路径，用于存储日志、
    缓存、配置等需要写入权限的文件。避免在程序安装目录写入
    导致的权限问题。
    
    Returns:
        str: 用户数据目录路径
        
    平台路径:
        - Windows: %APPDATA%/WeChatSpider
        - macOS: ~/Library/Application Support/WeChatSpider
        - Linux: ~/.local/share/WeChatSpider
    """
    if sys.platform == 'win32':
        app_data = os.environ.get('APPDATA', os.path.expanduser('~'))
        return os.path.join(app_data, 'WeChatSpider')
    elif sys.platform == 'darwin':
        return os.path.join(os.path.expanduser('~'), 'Library', 'Application Support', 'WeChatSpider')
    else:
        return os.path.join(os.path.expanduser('~'), '.local', 'share', 'WeChatSpider')


def setup_logger(log_file=None, log_level="INFO"):
    """
    配置并初始化日志记录器
    
    设置日志输出目标、格式和级别。支持同时输出到控制台和文件，
    自动处理打包环境下的特殊情况。
    
    Args:
        log_file: 日志文件路径，为 None 时仅输出到控制台
        log_level: 日志级别，可选 DEBUG/INFO/WARNING/ERROR/CRITICAL
    
    Returns:
        logger: 配置完成的 loguru logger 实例
    
    日志格式:
        控制台: 带颜色的时间戳 | 级别 | 模块:函数:行号 - 消息
        文件: 纯文本格式，便于日志分析工具处理
    
    自动轮转策略:
        - 单文件最大 10MB
        - 保留最近 1 周的日志
    """
    # 清除已有的处理器，避免重复输出
    logger.remove()
    
    # 控制台输出（GUI 打包后 stderr 可能为 None）
    if sys.stderr is not None:
        logger.add(
            sys.stderr,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level=log_level
        )
    
    # 打包环境自动启用文件日志
    if getattr(sys, 'frozen', False):
        user_data_dir = get_user_data_dir()
        default_log_file = os.path.join(user_data_dir, 'logs', 'app.log')
        log_dir = os.path.dirname(default_log_file)
        
        if not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
            
        logger.add(
            default_log_file,
            rotation="10 MB",
            retention="1 week",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level=log_level,
            encoding="utf-8"
        )
    
    # 自定义日志文件
    if log_file:
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        logger.add(
            log_file,
            rotation="10 MB",
            retention="1 week",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level=log_level,
            encoding="utf-8"
        )
    
    return logger


# 模块加载时自动初始化默认日志配置
logger = setup_logger()