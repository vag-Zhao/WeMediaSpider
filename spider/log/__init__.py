#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志模块
========

提供项目统一的日志记录功能，基于 loguru 库实现。
支持控制台输出和文件记录，自动处理日志轮转和清理。

导出:
    - setup_logger: 配置日志记录器的函数
    - logger: 预配置好的日志实例，可直接使用
"""

from .utils import setup_logger, logger

__all__ = ['setup_logger', 'logger']