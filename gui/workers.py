#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
后台工作线程模块

本模块提供 GUI 应用的后台工作线程，用于执行耗时的爬取任务，
避免阻塞主线程导致界面卡顿。

工作线程类型:
    1. BatchScrapeWorker: 同步爬取工作线程
       - 使用 ThreadPoolExecutor 实现并发
       - 适用于简单的批量爬取场景
    
    2. AsyncBatchScrapeWorker: 异步爬取工作线程
       - 使用 aiohttp 实现高效并发
       - 适用于大量公众号的批量爬取
       - 性能更好，资源占用更低

信号机制:
    两种工作线程都提供相同的信号接口，方便 GUI 层统一处理：
    - progress_update: 进度更新
    - account_status: 账号状态变化
    - scrape_success: 爬取成功
    - scrape_failed: 爬取失败
    - status_update: 状态文字更新
    - article_progress: 文章数量更新

使用方式:
    1. 创建工作线程实例，传入爬虫对象和配置
    2. 连接信号到 GUI 槽函数
    3. 调用 start() 启动线程
    4. 需要取消时调用 cancel()
"""

from PyQt6.QtCore import QThread, pyqtSignal
from datetime import datetime, timedelta
import time
import os


class BatchScrapeWorker(QThread):
    """同步批量爬取工作线程
    
    在后台线程中执行同步爬取任务，通过信号向 GUI 报告进度。
    
    Signals:
        progress_update(int, int, str): 进度更新，参数为 (当前值, 总值, 消息)
        account_status(str, str, str): 账号状态，参数为 (账号名, 状态, 消息)
        scrape_success(list, str): 爬取成功，参数为 (文章列表, 输出文件路径)
        scrape_failed(str): 爬取失败，参数为错误消息
        status_update(str): 状态文字更新
        article_progress(int, str): 文章进度，参数为 (文章数量, 消息)
    
    Attributes:
        batch_scraper: 批量爬虫实例
        config: 爬取配置字典
        is_cancelled: 是否已取消
        articles: 已爬取的文章列表
    """
    
    progress_update = pyqtSignal(int, int, str)
    account_status = pyqtSignal(str, str, str)
    scrape_success = pyqtSignal(list, str)
    scrape_failed = pyqtSignal(str)
    status_update = pyqtSignal(str)
    article_progress = pyqtSignal(int, str)
    
    def __init__(self, batch_scraper, config: dict):
        """初始化工作线程
        
        Args:
            batch_scraper: 批量爬虫实例，需要实现 start_batch_scrape 方法
            config: 爬取配置字典，包含公众号列表、文章数量等参数
        """
        super().__init__()
        self.batch_scraper = batch_scraper
        self.config = config
        self.is_cancelled = False
        self.articles = []  # 保存爬取的文章
    
    def cancel(self):
        """取消爬取任务
        
        设置取消标志并通知爬虫停止工作。
        已爬取的文章仍然可以通过 get_articles() 获取。
        """
        self.is_cancelled = True
        self.batch_scraper.cancel_batch_scrape()
    
    def get_articles(self) -> list:
        """获取已爬取的文章列表
        
        Returns:
            文章字典列表，即使任务被取消也会返回已获取的部分
        """
        return self.articles
    
    def run(self):
        """线程主函数，执行爬取任务"""
        try:
            # 设置回调
            def progress_callback(current, total):
                pass  # 不再使用公众号进度
            
            def account_status_callback(account_name, status, message):
                if not self.is_cancelled:
                    self.account_status.emit(account_name, status, message)
            
            def batch_completed_callback(total_articles):
                pass  # 由主线程处理
            
            def error_callback(account_name, error_message):
                if not self.is_cancelled:
                    self.account_status.emit(account_name, "error", error_message)
            
            def article_progress_callback(article_count, message):
                if not self.is_cancelled:
                    self.article_progress.emit(article_count, message)
                    # 使用文章数模式（total=0 表示不确定进度）
                    self.progress_update.emit(article_count, 0, message)
            
            def content_progress_callback(current, total, message):
                """ 真实百分比进度 """
                if not self.is_cancelled:
                    self.progress_update.emit(current, total, message)
            
            self.batch_scraper.set_callback('progress_updated', progress_callback)
            self.batch_scraper.set_callback('account_status', account_status_callback)
            self.batch_scraper.set_callback('batch_completed', batch_completed_callback)
            self.batch_scraper.set_callback('error_occurred', error_callback)
            self.batch_scraper.set_callback('article_progress', article_progress_callback)
            self.batch_scraper.set_callback('content_progress', content_progress_callback)
            
            # 开始爬取
            self.status_update.emit("开始爬取...")
            self.articles = self.batch_scraper.start_batch_scrape(self.config)
            
            if self.is_cancelled:
                self.scrape_failed.emit("已取消")
                return
            
            output_file = self.config.get('output_file', '')
            self.scrape_success.emit(self.articles, output_file)
            
        except Exception as e:
            self.scrape_failed.emit(f"批量爬取出错: {str(e)}")


class AsyncBatchScrapeWorker(QThread):
    """异步批量爬取工作线程
    
    使用 aiohttp 实现高效的异步并发爬取，相比同步版本：
    - 更高的并发性能
    - 更低的资源占用
    - 更好的网络利用率
    
    信号接口与 BatchScrapeWorker 完全相同，可以无缝替换。
    
    Signals:
        progress_update(int, int, str): 进度更新
        account_status(str, str, str): 账号状态
        scrape_success(list, str): 爬取成功
        scrape_failed(str): 爬取失败
        status_update(str): 状态更新
        article_progress(int, str): 文章进度
    
    Attributes:
        async_scraper: 异步爬虫实例
        config: 爬取配置字典
        is_cancelled: 是否已取消
        articles: 已爬取的文章列表
    """
    
    progress_update = pyqtSignal(int, int, str)
    account_status = pyqtSignal(str, str, str)
    scrape_success = pyqtSignal(list, str)
    scrape_failed = pyqtSignal(str)
    status_update = pyqtSignal(str)
    article_progress = pyqtSignal(int, str)
    
    def __init__(self, async_scraper, config: dict):
        """初始化异步工作线程
        
        Args:
            async_scraper: 异步爬虫实例
            config: 爬取配置字典
        """
        super().__init__()
        self.async_scraper = async_scraper
        self.config = config
        self.is_cancelled = False
        self.articles = []
    
    def cancel(self):
        """取消爬取任务"""
        self.is_cancelled = True
        self.async_scraper.cancel_batch_scrape()
    
    def get_articles(self) -> list:
        """获取已爬取的文章列表
        
        优先返回已完成的文章列表，如果任务被取消，
        会尝试从爬虫获取已收集的部分结果。
        
        Returns:
            文章字典列表
        """
        # 优先返回已完成的文章列表
        if self.articles:
            return self.articles
        # 如果爬取被取消，尝试从爬虫获取已收集的文章
        if hasattr(self.async_scraper, 'get_collected_articles'):
            return self.async_scraper.get_collected_articles()
        if hasattr(self.async_scraper, 'collected_articles'):
            return self.async_scraper.collected_articles
        return []
    
    def run(self):
        """线程主函数，执行异步爬取任务"""
        try:
            # 设置回调
            def progress_callback(current, total):
                pass  # 不再使用公众号进度
            
            def account_status_callback(account_name, status, message):
                if not self.is_cancelled:
                    self.account_status.emit(account_name, status, message)
            
            def batch_completed_callback(total_articles):
                pass  # 由主线程处理
            
            def error_callback(account_name, error_message):
                if not self.is_cancelled:
                    self.account_status.emit(account_name, "error", error_message)
            
            def article_progress_callback(article_count, message):
                if not self.is_cancelled:
                    self.article_progress.emit(article_count, message)
                    # 使用文章数模式（total=0 表示不确定进度）
                    self.progress_update.emit(article_count, 0, message)
            
            def content_progress_callback(current, total, message):
                """真实百分比进度"""
                if not self.is_cancelled:
                    self.progress_update.emit(current, total, message)
            
            # 设置回调
            self.async_scraper.set_callback('progress_updated', progress_callback)
            self.async_scraper.set_callback('account_status', account_status_callback)
            self.async_scraper.set_callback('batch_completed', batch_completed_callback)
            self.async_scraper.set_callback('error_occurred', error_callback)
            self.async_scraper.set_callback('article_progress', article_progress_callback)
            self.async_scraper.set_callback('content_progress', content_progress_callback)
            
            # 开始异步爬取
            self.status_update.emit("开始异步爬取...")
            self.articles = self.async_scraper.start_batch_scrape(self.config)
            
            if self.is_cancelled:
                self.scrape_failed.emit("已取消")
                return
            
            output_file = self.config.get('output_file', '')
            self.scrape_success.emit(self.articles, output_file)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.scrape_failed.emit(f"异步爬取出错: {str(e)}")
