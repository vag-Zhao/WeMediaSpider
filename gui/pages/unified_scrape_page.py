#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
公众号爬取页面模块

这是应用的核心功能页面，提供微信公众号文章爬取的完整界面。
支持单个公众号爬取和批量爬取（输入多个公众号名称即可）。

主要功能：
    - 公众号名称输入（支持多行批量输入）
    - 爬取参数配置（页数、间隔、并发数等）
    - 日期范围筛选
    - 正文内容获取（可选）
    - 正文关键词过滤
    - 实时爬取进度显示
    - 爬取状态表格展示

界面布局：
    - 左侧：公众号列表输入区域
    - 右侧：爬取配置和状态显示
    - 底部：进度条和操作按钮

技术实现：
    - 使用异步爬虫 AsyncBatchWeChatScraper 进行数据抓取
    - 通过 QThread 工作线程避免界面阻塞
    - 支持爬取过程中取消操作
    - 自动保存爬取结果到 CSV 文件
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QHeaderView, QFileDialog, QTableWidgetItem,
    QGridLayout, QFrame
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QColor
from datetime import datetime
import os
import json

from qfluentwidgets import (
    TitleLabel, BodyLabel, CaptionLabel, CardWidget,
    PrimaryPushButton, PushButton, LineEdit,
    DatePicker, CheckBox, InfoBar, InfoBarPosition, FluentIcon,
    PickerColumnFormatter
)
from qfluentwidgets import TableWidget as FluentTable

from ..styles import COLORS
from ..widgets import CardWidget as CustomCard, ProgressWidget, AccountListWidget, CustomSpinBox
from ..workers import AsyncBatchScrapeWorker
from ..utils import DEFAULT_OUTPUT_DIR, play_sound
from spider.wechat.scraper import AsyncBatchWeChatScraper

# ============================================================
# 配置常量定义
# ============================================================

# 配置文件路径，与设置页面共用同一个配置文件
CONFIG_FILE = 'config.json'

# 默认爬取配置参数
# 这些值会在用户首次使用时生效，之后会从配置文件加载
DEFAULT_CONFIG = {
    'max_pages': 10,           # 每个公众号最多爬取的页数
    'request_interval': 10,    # 请求间隔（秒），避免触发反爬
    'max_workers': 5,          # 最大并发数
    'include_content': False,  # 是否获取文章正文内容
    'output_dir': DEFAULT_OUTPUT_DIR,  # 输出目录，使用用户文档目录避免权限问题
    'cache_expire_hours': 96,  # 登录缓存有效期（小时）
}


class NumericMonthFormatter(PickerColumnFormatter):
    """
    月份数字格式化器
    
    qfluentwidgets 的 DatePicker 默认显示英文月份名（January, February...），
    这个格式化器将其改为显示数字（1, 2, 3...），更符合中文用户习惯。
    
    使用方式：
        date_picker.setColumnFormatter(0, NumericMonthFormatter())
    """
    
    def encode(self, value):
        """
        编码：将月份数值转换为显示字符串
        
        Args:
            value: 月份数值（1-12）
            
        Returns:
            str: 月份的字符串表示
        """
        return str(value)
    
    def decode(self, value: str):
        """
        解码：将显示字符串转换回月份数值
        
        Args:
            value: 月份字符串
            
        Returns:
            int: 月份数值
        """
        return int(value)


class UnifiedScrapePage(QWidget):
    """
    公众号爬取页面
    
    这是应用的主要功能页面，提供完整的公众号文章爬取功能。
    采用紧凑的单屏布局设计，无需滚动即可看到所有控件。
    
    Signals:
        scrape_completed: 爬取完成信号
            参数: (articles_list, source_info, temp_file_path)
    
    Attributes:
        login_manager: 登录管理器，用于获取登录凭证
        batch_scraper: 异步批量爬虫实例
        scrape_worker: 爬取工作线程
        config: 当前配置字典
    """
    
    # 爬取完成信号，用于通知主窗口跳转到结果页面
    scrape_completed = pyqtSignal(list, str, str)
    
    def __init__(self, login_manager, parent=None):
        """
        初始化爬取页面
        
        Args:
            login_manager: 登录管理器实例，提供登录状态和凭证
            parent: 父控件
        """
        super().__init__(parent)
        
        # 保存登录管理器引用
        self.login_manager = login_manager
        
        # 爬虫相关实例，在开始爬取时创建
        self.batch_scraper = None
        self.scrape_worker = None
        
        # 当前爬取任务的输出文件路径
        self._current_output_file = None
        
        # 设置对象名称，用于样式表选择器
        self.setObjectName("unifiedScrapePage")
        
        # 强制设置暗黑背景色
        self.setStyleSheet("background-color: #1a1a1a;")
        
        # 加载配置：先使用默认值，再从文件覆盖
        self.config = DEFAULT_CONFIG.copy()
        self._load_config()
        
        # 构建界面
        self._setup_ui()
        
        # 将配置值应用到界面控件
        self._apply_config_to_ui()
    
    def _setup_ui(self):
        """
        构建页面界面
        
        创建整体布局结构：
        1. 顶部标题
        2. 中间主内容区（左右分栏）
        3. 底部进度和按钮区
        """
        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(10)
        
        # 页面标题
        title = TitleLabel("公众号爬取")
        layout.addWidget(title)
        
        # 主内容区域 - 水平布局
        content_layout = QHBoxLayout()
        content_layout.setSpacing(12)
        
        # 左侧：公众号输入区域
        self._setup_input_area(content_layout)
        
        # 右侧：配置和状态区域
        self._setup_config_area(content_layout)
        
        layout.addLayout(content_layout, 1)
        
        # 底部区域 - 进度和按钮
        bottom_layout = QVBoxLayout()
        bottom_layout.setSpacing(8)
        
        # 进度区域
        self.progress_card = CustomCard("爬取进度")
        self.progress_widget = ProgressWidget()
        self.progress_card.addWidget(self.progress_widget)
        self.progress_card.hide()
        self.progress_card.setFixedHeight(120)  # 足够显示所有内容
        bottom_layout.addWidget(self.progress_card)
        
        # 保存爬取状态
        self._total_accounts = 0
        self._current_account_index = 0
        self._article_count = 0
        
        # 操作按钮行 - 开始爬取和取消按钮在同一行，右对齐
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        # 取消按钮 - 初始隐藏
        self.cancel_btn = PushButton("取消爬取", icon=FluentIcon.CLOSE)
        self.cancel_btn.setFixedWidth(120)
        self.cancel_btn.clicked.connect(self._on_cancel)
        self.cancel_btn.hide()
        btn_layout.addWidget(self.cancel_btn)
        
        self.start_btn = PrimaryPushButton("开始爬取", icon=FluentIcon.PLAY)
        self.start_btn.setFixedWidth(140)
        self.start_btn.clicked.connect(self._on_start_scrape)
        btn_layout.addWidget(self.start_btn)
        bottom_layout.addLayout(btn_layout)
        
        layout.addLayout(bottom_layout)
    
    def _setup_input_area(self, parent_layout):
        """
        设置公众号输入区域（左侧面板）
        
        包含：
        - 区域标题
        - 输入提示
        - 公众号列表输入控件（支持多行输入和历史记录）
        
        Args:
            parent_layout: 父布局，用于添加输入卡片
        """
        # 输入区域卡片
        input_card = CardWidget()
        input_layout = QVBoxLayout(input_card)
        input_layout.setContentsMargins(16, 12, 16, 12)
        input_layout.setSpacing(8)
        
        input_title = BodyLabel("公众号列表")
        input_title.setStyleSheet("font-weight: bold; font-size: 13px; color: #0078d4;")
        input_layout.addWidget(input_title)
        
        hint = CaptionLabel("每行一个公众号名称，支持批量爬取")
        hint.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 11px;")
        input_layout.addWidget(hint)
        
        # AccountListWidget 已内置清空按钮和历史记录功能
        self.account_list = AccountListWidget()
        input_layout.addWidget(self.account_list, 1)
        
        parent_layout.addWidget(input_card, 1)
    
    def _setup_config_area(self, parent_layout):
        """
        设置配置和状态区域（右侧面板）
        
        包含两个卡片：
        1. 爬取配置卡片 - 各种爬取参数设置
        2. 爬取状态卡片 - 显示各公众号的爬取状态
        
        配置项采用网格布局，紧凑排列：
        - 第一行：最大页数 | 请求间隔
        - 第二行：日期范围选择
        - 第三行：并发数 | 获取正文选项
        - 第四行：正文过滤 | 输出目录
        
        Args:
            parent_layout: 父布局
        """
        # 右侧容器
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)
        
        # ===== 爬取配置卡片（合并基础和高级配置）=====
        config_card = CardWidget()
        config_layout = QVBoxLayout(config_card)
        config_layout.setContentsMargins(16, 12, 16, 12)
        config_layout.setSpacing(10)
        
        config_title = BodyLabel("爬取配置")
        config_title.setStyleSheet("font-weight: bold; font-size: 13px; color: #0078d4;")
        config_layout.addWidget(config_title)
        
        # 使用网格布局 - 更紧凑
        grid = QGridLayout()
        grid.setSpacing(8)
        grid.setContentsMargins(0, 0, 0, 0)
        
        # 第一行：最大页数 | 请求间隔
        grid.addWidget(BodyLabel("最大页数"), 0, 0)
        self.pages_spin = CustomSpinBox(1, 100, self.config.get('max_pages', 10))
        self.pages_spin.setFixedWidth(120)  # 增加宽度避免重叠
        grid.addWidget(self.pages_spin, 0, 1)
        
        grid.addWidget(BodyLabel("请求间隔"), 0, 2)
        interval_container = QHBoxLayout()
        interval_container.setSpacing(4)
        self.interval_spin = CustomSpinBox(1, 60, self.config.get('request_interval', 10))
        self.interval_spin.setFixedWidth(120)  # 增加宽度避免重叠
        interval_container.addWidget(self.interval_spin)
        interval_unit = BodyLabel("秒")
        interval_unit.setStyleSheet("color: #888; font-size: 12px;")
        interval_container.addWidget(interval_unit)
        interval_container.addStretch()
        grid.addLayout(interval_container, 0, 3)
        
        # 第二行：日期范围
        grid.addWidget(BodyLabel("日期范围"), 1, 0)
        date_container = QHBoxLayout()
        date_container.setSpacing(6)
        self.start_date = DatePicker()
        self.start_date.setColumnFormatter(0, NumericMonthFormatter())  # 月份使用数字格式
        self.start_date.setColumnWidth(0, 50)  # 缩小月份列宽度
        self.start_date.setDate(QDate.currentDate().addDays(-30))
        date_container.addWidget(self.start_date)
        date_sep = BodyLabel("→")
        date_sep.setFixedWidth(16)
        date_sep.setAlignment(Qt.AlignmentFlag.AlignCenter)
        date_container.addWidget(date_sep)
        self.end_date = DatePicker()
        self.end_date.setColumnFormatter(0, NumericMonthFormatter())  # 月份使用数字格式
        self.end_date.setColumnWidth(0, 50)  # 缩小月份列宽度
        self.end_date.setDate(QDate.currentDate())
        date_container.addWidget(self.end_date)
        date_container.addStretch()
        grid.addLayout(date_container, 1, 1, 1, 3)
        
        # 第三行：并发数 | 获取正文
        grid.addWidget(BodyLabel("并发数"), 2, 0)
        concurrent_container = QHBoxLayout()
        concurrent_container.setSpacing(4)
        self.concurrent_spin = CustomSpinBox(1, 10, self.config.get('max_workers', 5))
        self.concurrent_spin.setFixedWidth(110)
        self.concurrent_spin.setToolTip("每个公众号的最大并发请求数")
        concurrent_container.addWidget(self.concurrent_spin)
        concurrent_unit = BodyLabel("并发")
        concurrent_unit.setStyleSheet("color: #888; font-size: 12px;")
        concurrent_container.addWidget(concurrent_unit)
        concurrent_container.addStretch()
        grid.addLayout(concurrent_container, 2, 1)
        
        self.content_check = CheckBox("获取正文内容（较慢）")
        self.content_check.setChecked(self.config.get('include_content', False))
        self.content_check.stateChanged.connect(self._on_content_check_changed)
        # 强制设置 CheckBox 透明背景
        self.content_check.setStyleSheet("""
            CheckBox, QCheckBox {
                background-color: transparent;
                background: transparent;
                color: #ffffff;
            }
            CheckBox::indicator, QCheckBox::indicator {
                background-color: #3d3d3d;
                border: 1px solid #555555;
                border-radius: 3px;
            }
            CheckBox::indicator:checked, QCheckBox::indicator:checked {
                background-color: #07C160;
                border-color: #07C160;
            }
        """)
        grid.addWidget(self.content_check, 2, 2, 1, 2)
        
        config_layout.addLayout(grid)
        
        # 第四行：正文过滤 | 输出目录（对称布局）
        grid.addWidget(BodyLabel("正文过滤"), 3, 0)
        self.keyword_filter_input = LineEdit()
        self.keyword_filter_input.setPlaceholderText("输入关键词过滤正文")
        self.keyword_filter_input.setEnabled(self.config.get('include_content', False))
        self.keyword_filter_input.setToolTip("只保留正文中包含该关键词的文章（需勾选获取正文）")
        self.keyword_filter_input.setMaximumWidth(200)
        grid.addWidget(self.keyword_filter_input, 3, 1)
        
        grid.addWidget(BodyLabel("输出目录"), 3, 2)
        output_container = QHBoxLayout()
        output_container.setSpacing(4)
        self.output_input = LineEdit()
        # 获取配置中的输出目录，如果是旧值 'results' 则使用新的默认路径
        config_output_dir = self.config.get('output_dir', DEFAULT_OUTPUT_DIR)
        if config_output_dir == 'results':
            config_output_dir = DEFAULT_OUTPUT_DIR
        self.output_input.setText(config_output_dir)
        self.output_input.setPlaceholderText("输出目录")
        self.output_input.setMaximumWidth(100)
        output_container.addWidget(self.output_input)
        browse_btn = PushButton("...", icon=FluentIcon.FOLDER)
        browse_btn.setFixedWidth(50)
        browse_btn.setToolTip("浏览选择输出目录")
        browse_btn.clicked.connect(self._on_browse_output)
        output_container.addWidget(browse_btn)
        output_container.addStretch()
        grid.addLayout(output_container, 3, 3)
        
        right_layout.addWidget(config_card)
        
        # ===== 爬取状态卡片 =====
        status_card = CardWidget()
        status_layout = QVBoxLayout(status_card)
        status_layout.setContentsMargins(16, 10, 16, 10)
        status_layout.setSpacing(6)
        
        status_header = QHBoxLayout()
        status_title = BodyLabel("爬取状态")
        status_title.setStyleSheet("font-weight: bold; font-size: 13px; color: #0078d4;")
        status_header.addWidget(status_title)
        status_header.addStretch()
        self.status_hint = CaptionLabel("等待开始...")
        self.status_hint.setStyleSheet("color: #888; font-size: 11px;")
        status_header.addWidget(self.status_hint)
        status_layout.addLayout(status_header)
        
        self.status_table = FluentTable()
        self.status_table.setColumnCount(3)
        self.status_table.setHorizontalHeaderLabels(["公众号", "状态", "详情"])
        # 三列等宽
        self.status_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.status_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.status_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        # 表头居中对齐
        self.status_table.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_table.setMinimumHeight(80)
        self.status_table.verticalHeader().setVisible(False)
        status_layout.addWidget(self.status_table, 1)
        
        right_layout.addWidget(status_card, 1)
        parent_layout.addWidget(right_container, 1)
    
    def _on_content_check_changed(self, state):
        """
        获取正文复选框状态变化处理
        
        当用户勾选或取消"获取正文内容"选项时，
        同步更新正文关键词过滤输入框的启用状态。
        
        Args:
            state: 复选框状态值
        """
        is_checked = state == Qt.CheckState.Checked.value
        self.keyword_filter_input.setEnabled(is_checked)
        if not is_checked:
            self.keyword_filter_input.clear()
    
    def _on_browse_output(self):
        """选择输出目录"""
        dir_path = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if dir_path:
            self.output_input.setText(dir_path)
    
    def _on_start_scrape(self):
        """开始爬取"""
        accounts = self.account_list.get_accounts()
        if not accounts:
            InfoBar.warning(title="提示", content="请输入公众号名称", parent=self, position=InfoBarPosition.TOP, duration=2000)
            return
        if not self.login_manager.is_logged_in():
            InfoBar.warning(title="未登录", content="请先登录微信公众平台", parent=self, position=InfoBarPosition.TOP, duration=3000)
            return
        
        token = self.login_manager.get_token()
        headers = self.login_manager.get_headers()
        if not token or not headers:
            InfoBar.warning(title="登录失效", content="请重新登录", parent=self, position=InfoBarPosition.TOP, duration=3000)
            return
        
        output_dir = self.output_input.text().strip() or DEFAULT_OUTPUT_DIR
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 根据公众号数量生成文件名
        if len(accounts) == 1:
            # 单个公众号：公众号名_时间戳.csv
            # 清理文件名中的非法字符
            safe_name = "".join(c for c in accounts[0] if c not in r'\/:*?"<>|')
            output_file = os.path.join(output_dir, f"{safe_name}_{timestamp}.csv")
        else:
            # 多个公众号：批量爬取_N个公众号_时间戳.csv
            output_file = os.path.join(output_dir, f"批量爬取_{len(accounts)}个公众号_{timestamp}.csv")
        self._current_output_file = output_file  # 记录当前输出文件路径
        
        # 获取正文关键词过滤
        keyword_filter = self.keyword_filter_input.text().strip() if self.content_check.isChecked() else ""
        
        # 使用异步模式
        config = {
            'accounts': accounts,
            'start_date': self.start_date.date.toString("yyyy-MM-dd"),
            'end_date': self.end_date.date.toString("yyyy-MM-dd"),
            'token': token, 'headers': headers,
            'max_pages_per_account': self.pages_spin.value(),
            'request_interval': self.interval_spin.value(),
            'include_content': self.content_check.isChecked(),
            'content_keyword_filter': keyword_filter,  # 正文关键词过滤
            'output_file': output_file,
            'max_concurrent_accounts': min(3, len(accounts)),  # 最多3个公众号并发
            'max_concurrent_requests': self.concurrent_spin.value()
        }
        
        # 初始化状态表格
        self.status_table.setRowCount(len(accounts))
        for i, acc in enumerate(accounts):
            # 创建居中对齐的单元格
            item0 = QTableWidgetItem(acc)
            item0.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.status_table.setItem(i, 0, item0)
            
            item1 = QTableWidgetItem("等待中")
            item1.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.status_table.setItem(i, 1, item1)
            
            item2 = QTableWidgetItem("")
            item2.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.status_table.setItem(i, 2, item2)
        
        # 更新状态提示
        self.status_hint.setText(f"正在爬取 {len(accounts)} 个公众号...")
        self.status_hint.setStyleSheet("color: #0078d4;")
        
        # 显示进度和取消按钮
        self.progress_card.show()
        self.progress_widget.reset()
        self.start_btn.hide()
        self.cancel_btn.show()
        
        # 初始化爬取状态
        self._total_accounts = len(accounts)
        self._current_account_index = 0
        self._article_count = 0
        
        # 启动爬取 - 使用异步爬虫
        self.batch_scraper = AsyncBatchWeChatScraper()
        self.scrape_worker = AsyncBatchScrapeWorker(self.batch_scraper, config)
        self.scrape_worker.progress_update.connect(self._on_progress_update)
        self.scrape_worker.account_status.connect(self._on_account_status)
        self.scrape_worker.scrape_success.connect(self._on_scrape_success)
        self.scrape_worker.scrape_failed.connect(self._on_scrape_failed)
        self.scrape_worker.status_update.connect(self._on_status_update)
        self.scrape_worker.article_progress.connect(self._on_article_progress)
        self.scrape_worker.start()
    
    def _on_progress_update(self, current, total, message):
        """更新进度显示"""
        if total > 0:
            # 真实百分比进度模式（获取正文内容时）
            self.progress_widget.set_progress(current, total, message)
            # 同时更新文章数量显示
            self.progress_widget.update_article_count(self._article_count)
        else:
            # 文章数量模式 - 使用动画进度条
            self._article_count = current
            self.progress_widget.set_article_progress(current, message)
    
    def _on_article_progress(self, article_count, message):
        """更新文章进度"""
        self._article_count = article_count
        self.progress_widget.set_article_progress(article_count, message)
    
    def _on_status_update(self, message):
        self.progress_widget.progress_label.setText(message)
    
    def _on_account_status(self, account_name, status, message):
        """更新账号爬取状态"""
        status_map = {
            'searching': '搜索中', 'fetching': '获取中', 'filtering': '过滤中',
            'content': '获取内容', 'completed': '完成', 'error': '失败', 'processing': '处理中'
        }
        
        # 更新当前账号索引
        if status in ['searching', 'fetching']:
            for row in range(self.status_table.rowCount()):
                item = self.status_table.item(row, 0)
                if item and item.text() == account_name:
                    self._current_account_index = row + 1
                    break
        
        for row in range(self.status_table.rowCount()):
            item = self.status_table.item(row, 0)
            if item and item.text() == account_name:
                # 更新状态列
                status_item = self.status_table.item(row, 1)
                status_item.setText(status_map.get(status, status))
                status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                color = COLORS['success'] if status == 'completed' else COLORS['error'] if status == 'error' else COLORS['warning']
                status_item.setForeground(QColor(color))
                
                # 更新详情列
                detail_item = self.status_table.item(row, 2)
                detail_item.setText(message)
                detail_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                break
    
    def _on_scrape_success(self, articles, output_file):
        self.start_btn.show()
        self.cancel_btn.hide()
        self._article_count = len(articles)
        self.progress_widget._article_count = len(articles)  # 确保完成时显示正确数量
        self.progress_widget.set_complete(f"爬取完成！")
        self.status_hint.setText(f"完成！共 {len(articles)} 篇文章")
        self.status_hint.setStyleSheet(f"color: {COLORS['success']};")
        
        # 播放任务完成音效
        play_sound('complete')
        
        # 保存公众号到历史记录
        accounts = self.account_list.get_accounts()
        if accounts:
            self.account_list.add_to_history(accounts)
        
        # 发射信号，跳转到结果页面，传递临时文件路径
        if len(accounts) == 1:
            source_info = f"爬取: {accounts[0]}"
        else:
            accounts_str = ', '.join(accounts[:3]) + ('...' if len(accounts) > 3 else '')
            source_info = f"批量爬取: {accounts_str} (共{len(accounts)}个公众号)"
        
        # 传递临时文件路径，以便用户放弃时可以删除
        temp_file = self._current_output_file or output_file
        self.scrape_completed.emit(articles, source_info, temp_file)
    
    def _on_scrape_failed(self, error_msg):
        self.start_btn.show()
        self.cancel_btn.hide()
        self.progress_card.hide()
        self.status_hint.setText("爬取失败")
        self.status_hint.setStyleSheet(f"color: {COLORS['error']};")
        if error_msg != "已取消":
            InfoBar.error(title="爬取失败", content=error_msg, parent=self, position=InfoBarPosition.TOP, duration=5000)
    
    def _on_cancel(self):
        """取消爬取"""
        articles_before_cancel = []
        if self.scrape_worker:
            if hasattr(self.scrape_worker, 'get_articles'):
                articles_before_cancel = self.scrape_worker.get_articles()
            self.scrape_worker.cancel()
            self.scrape_worker = None
        
        self.start_btn.show()
        self.cancel_btn.hide()
        self.progress_widget.progress_label.setText("已取消")
        self.status_hint.setText("已取消")
        self.status_hint.setStyleSheet("color: #888;")
        
        # 如果有已爬取的数据，也跳转到结果页面
        if articles_before_cancel:
            accounts = self.account_list.get_accounts()
            if len(accounts) == 1:
                source_info = f"爬取(已取消): {accounts[0]}"
            else:
                accounts_str = ', '.join(accounts[:3]) + ('...' if len(accounts) > 3 else '')
                source_info = f"批量爬取(已取消): {accounts_str}"
            # 传递临时文件路径
            temp_file = self._current_output_file or ""
            self.scrape_completed.emit(articles_before_cancel, source_info, temp_file)
    
    def _load_config(self):
        """从配置文件加载设置"""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    self.config.update(json.load(f))
            except Exception:
                pass
    
    def _apply_config_to_ui(self):
        """将配置应用到UI控件"""
        # 这个方法在 _setup_ui 之后调用，确保控件已创建
        # 由于控件在创建时已经使用了配置值，这里主要用于后续的设置更新
        pass
    
    def apply_settings(self, config: dict):
        """应用设置页面的配置
        
        Args:
            config: 设置页面传递的配置字典
        """
        # 更新本地配置
        self.config.update(config)
        
        # 应用到UI控件
        if 'max_pages' in config:
            self.pages_spin.setValue(config['max_pages'])
        
        if 'request_interval' in config:
            self.interval_spin.setValue(config['request_interval'])
        
        if 'max_workers' in config:
            self.concurrent_spin.setValue(config['max_workers'])
        
        if 'include_content' in config:
            self.content_check.setChecked(config['include_content'])
            # 同时更新关键词过滤输入框的启用状态
            self.keyword_filter_input.setEnabled(config['include_content'])
            if not config['include_content']:
                self.keyword_filter_input.clear()
        
        if 'output_dir' in config:
            self.output_input.setText(config['output_dir'])
