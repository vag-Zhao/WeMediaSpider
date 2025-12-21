#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
结果查看页面模块

提供爬取结果的查看、筛选、导出功能。采用 Fluent Design 风格设计。

主要功能：
    - 加载和显示爬取结果数据
    - 支持从文件加载历史数据
    - 按公众号筛选文章
    - 关键词搜索标题
    - 双击预览文章内容
    - 右键菜单操作（预览、打开链接、图片提取）
    - 多格式导出（CSV、JSON、Excel、Markdown、HTML）
    - 未保存数据提醒和放弃确认

界面布局：
    - 顶部：数据来源信息和操作按钮
    - 中部：文件选择和快速打开
    - 筛选栏：搜索框和公众号过滤
    - 主体：文章数据表格
    - 底部：打开结果目录按钮

技术特点：
    - 支持直接加载爬取结果（无需保存文件）
    - 临时文件管理（放弃时自动删除）
    - HTML 导出支持单篇文章浏览和键盘导航
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QHeaderView, QFileDialog, QTableWidgetItem, QAbstractItemView, QMenu
from PyQt6.QtCore import Qt, QUrl, pyqtSignal
from PyQt6.QtGui import QDesktopServices, QAction
import os
import csv
import json

from qfluentwidgets import ScrollArea, TitleLabel, BodyLabel, CardWidget, PrimaryPushButton, PushButton, LineEdit, ComboBox, InfoBar, InfoBarPosition, FluentIcon, MessageBox
from qfluentwidgets import TableWidget as FluentTable

from ..styles import COLORS
from ..widgets import ArticlePreviewDialog
from ..utils import DEFAULT_OUTPUT_DIR

# ============================================================
# 导出格式配置
# ============================================================

# 支持的导出文件格式
# 键: 格式标识符
# 值: (格式名称, 文件扩展名)
SUPPORTED_FORMATS = {
    'csv': ('CSV文件', '.csv'),      # 通用表格格式，Excel可直接打开
    'json': ('JSON文件', '.json'),   # 结构化数据格式，便于程序处理
    'xlsx': ('Excel文件', '.xlsx'),  # Excel原生格式，需要pandas和openpyxl
    'md': ('Markdown文件', '.md'),   # 文档格式，便于阅读和分享
    'html': ('HTML文件', '.html'),   # 网页格式，支持交互式浏览
}


class ResultsPage(ScrollArea):
    """
    结果查看页面
    
    显示爬取结果数据，支持筛选、搜索、预览和导出功能。
    可以直接加载爬取结果，也可以从文件加载历史数据。
    
    Signals:
        data_discarded: 用户放弃未保存数据时发射
        extract_images_requested: 请求提取文章图片时发射，参数为文章链接
    
    Attributes:
        current_file: 当前加载的文件路径
        articles: 文章数据列表
        is_unsaved: 是否有未保存的数据
        source_info: 数据来源描述
        temp_file_path: 临时文件路径（用于放弃时删除）
    """
    
    # 放弃数据信号 - 通知主窗口用户放弃了数据
    data_discarded = pyqtSignal()
    # 图片提取信号 - 通知主窗口跳转到图片提取页面并填充链接
    extract_images_requested = pyqtSignal(str)
    
    def __init__(self, parent=None):
        """
        初始化结果页面
        
        Args:
            parent: 父控件
        """
        super().__init__(parent)
        
        # 当前加载的文件路径
        self.current_file = None
        # 文章数据列表，每篇文章是一个字典
        self.articles = []
        # 标记是否有未保存的数据（从爬取结果直接加载时为True）
        self.is_unsaved = False
        # 数据来源描述信息
        self.source_info = ""
        # 临时文件路径，爬取时自动保存的文件，用户放弃时需要删除
        self.temp_file_path = None
        
        # 设置对象名称，用于样式表选择器
        self.setObjectName("resultsPage")
        
        # 强制设置暗黑背景样式
        self.setStyleSheet("""
            QScrollArea#resultsPage {
                background-color: #1a1a1a;
                border: none;
            }
            QScrollArea#resultsPage > QWidget > QWidget {
                background-color: #1a1a1a;
            }
        """)
        
        self._setup_ui()
    
    def _setup_ui(self):
        """
        构建页面界面
        
        创建完整的结果查看界面，包括：
        - 数据来源信息卡片
        - 文件选择区域
        - 筛选工具栏
        - 数据表格
        - 操作按钮
        """
        self.setWidgetResizable(True)
        container = QWidget()
        self.setWidget(container)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(36, 20, 36, 36)
        layout.setSpacing(20)
        
        # 页面标题
        layout.addWidget(TitleLabel("结果查看"))
        
        # 数据来源提示框（用于显示爬取结果）
        self.source_card = CardWidget()
        source_layout = QHBoxLayout(self.source_card)
        source_layout.setContentsMargins(20, 15, 20, 15)
        self.source_label = BodyLabel("数据来源: 未加载")
        self.source_label.setStyleSheet(f"color: {COLORS['primary']}; font-weight: bold;")
        source_layout.addWidget(self.source_label)
        source_layout.addStretch()
        
        # 放弃按钮 - 丢弃未保存的数据
        self.discard_btn = PushButton("放弃数据", icon=FluentIcon.DELETE)
        self.discard_btn.setFixedWidth(120)
        self.discard_btn.clicked.connect(self._on_discard_data)
        self.discard_btn.hide()  # 默认隐藏
        source_layout.addWidget(self.discard_btn)
        
        # 保存按钮
        self.save_btn = PrimaryPushButton("保存结果", icon=FluentIcon.SAVE)
        self.save_btn.setFixedWidth(140)
        self.save_btn.clicked.connect(self._on_save_results)
        self.save_btn.hide()  # 默认隐藏，有未保存数据时显示
        source_layout.addWidget(self.save_btn)
        self.source_card.hide()  # 默认隐藏
        layout.addWidget(self.source_card)
        
        file_card = CardWidget()
        file_layout = QVBoxLayout(file_card)
        file_layout.setContentsMargins(20, 20, 20, 20)
        file_layout.setSpacing(12)
        file_title = BodyLabel("数据文件")
        file_title.setStyleSheet("font-weight: bold; font-size: 15px; color: #ffffff;")
        file_layout.addWidget(file_title)
        
        input_layout = QHBoxLayout()
        self.file_input = LineEdit()
        self.file_input.setPlaceholderText("选择CSV文件...")
        self.file_input.setReadOnly(True)
        input_layout.addWidget(self.file_input, 1)  # stretch factor 1，自动填充剩余空间
        browse_btn = PushButton("浏览", icon=FluentIcon.FOLDER)
        browse_btn.setFixedWidth(100)
        browse_btn.clicked.connect(self._on_browse_file)
        input_layout.addWidget(browse_btn)
        load_btn = PrimaryPushButton("加载", icon=FluentIcon.DOWNLOAD)
        load_btn.setFixedWidth(100)
        load_btn.clicked.connect(self._on_load_file)
        input_layout.addWidget(load_btn)
        file_layout.addLayout(input_layout)
        
        recent_layout = QHBoxLayout()
        recent_label = BodyLabel("快速打开:")
        recent_label.setFixedWidth(70)  # 固定标签宽度
        recent_layout.addWidget(recent_label)
        self.recent_combo = ComboBox()
        self._update_recent_files()
        recent_layout.addWidget(self.recent_combo, 1)  # stretch factor 1，与上面的输入框对齐
        open_btn = PushButton("打开", icon=FluentIcon.FOLDER)
        open_btn.setFixedWidth(100)
        open_btn.clicked.connect(self._on_open_recent)
        recent_layout.addWidget(open_btn)
        refresh_btn = PushButton("刷新", icon=FluentIcon.SYNC)
        refresh_btn.setFixedWidth(100)
        refresh_btn.clicked.connect(self._update_recent_files)
        recent_layout.addWidget(refresh_btn)
        file_layout.addLayout(recent_layout)
        layout.addWidget(file_card)
        
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(BodyLabel("搜索:"))
        self.search_input = LineEdit()
        self.search_input.setPlaceholderText("输入关键词搜索标题...")
        self.search_input.textChanged.connect(self._on_search)
        self.search_input.setMaximumWidth(300)
        filter_layout.addWidget(self.search_input)
        filter_layout.addWidget(BodyLabel("公众号:"))
        self.account_filter = ComboBox()
        self.account_filter.addItem("全部")
        self.account_filter.currentTextChanged.connect(self._on_filter_changed)
        self.account_filter.setMinimumWidth(150)
        filter_layout.addWidget(self.account_filter)
        filter_layout.addStretch()
        self.count_label = BodyLabel("共 0 条记录")
        filter_layout.addWidget(self.count_label)
        layout.addLayout(filter_layout)
        
        self.data_table = FluentTable()
        self.data_table.setColumnCount(3)
        self.data_table.setHorizontalHeaderLabels(["公众号", "标题", "发布时间"])
        self.data_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.data_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.data_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.data_table.itemSelectionChanged.connect(self._on_selection_changed)
        self.data_table.doubleClicked.connect(self._on_table_double_clicked)
        # 禁用双击编辑功能
        self.data_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        # 启用右键菜单
        self.data_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.data_table.customContextMenuRequested.connect(self._on_context_menu)
        layout.addWidget(self.data_table, 1)
        
        # 创建全屏预览对话框
        self.preview_dialog = None
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        open_folder_btn = PushButton("打开结果目录", icon=FluentIcon.FOLDER)
        open_folder_btn.clicked.connect(self._on_open_folder)
        btn_layout.addWidget(open_folder_btn)
        layout.addLayout(btn_layout)
    
    def _update_recent_files(self):
        self.recent_combo.clear()
        self.recent_combo.addItem("选择文件...")
        results_dir = DEFAULT_OUTPUT_DIR
        if os.path.exists(results_dir):
            csv_files = [(f, os.path.join(results_dir, f), os.path.getmtime(os.path.join(results_dir, f))) for f in os.listdir(results_dir) if f.endswith('.csv')]
            csv_files.sort(key=lambda x: x[2], reverse=True)
            for name, path, _ in csv_files[:10]:
                self.recent_combo.addItem(name, userData=path)
    
    def _on_browse_file(self):
        # 导入默认输出目录
        from gui.utils import DEFAULT_OUTPUT_DIR
        file_path, _ = QFileDialog.getOpenFileName(self, "选择CSV文件", DEFAULT_OUTPUT_DIR, "CSV文件 (*.csv)")
        if file_path:
            self.file_input.setText(file_path)
    
    def _on_load_file(self):
        file_path = self.file_input.text().strip()
        if not file_path:
            InfoBar.warning(title="提示", content="请先选择文件", parent=self, position=InfoBarPosition.TOP, duration=2000)
            return
        self._load_csv_file(file_path)
    
    def _on_open_recent(self):
        index = self.recent_combo.currentIndex()
        if index <= 0:
            return
        file_path = self.recent_combo.currentData()
        if file_path and os.path.exists(file_path):
            self.file_input.setText(file_path)
            self._load_csv_file(file_path)
        else:
            InfoBar.warning(title="文件不存在", content="所选文件不存在", parent=self, position=InfoBarPosition.TOP, duration=2000)
    
    def _load_csv_file(self, file_path):
        try:
            self.articles = []
            accounts = set()
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.articles.append(row)
                    if '公众号' in row:
                        accounts.add(row['公众号'])
            self.current_file = file_path
            self.account_filter.clear()
            self.account_filter.addItem("全部")
            for account in sorted(accounts):
                self.account_filter.addItem(account)
            self._display_articles(self.articles)
            InfoBar.success(title="加载成功", content=f"成功加载 {len(self.articles)} 条记录", parent=self, position=InfoBarPosition.TOP, duration=3000)
        except Exception as e:
            InfoBar.error(title="加载失败", content=str(e), parent=self, position=InfoBarPosition.TOP, duration=3000)
    
    def _display_articles(self, articles):
        self.data_table.setRowCount(len(articles))
        for i, article in enumerate(articles):
            self.data_table.setItem(i, 0, QTableWidgetItem(article.get('公众号', '')))
            self.data_table.setItem(i, 1, QTableWidgetItem(article.get('标题', '')))
            self.data_table.setItem(i, 2, QTableWidgetItem(article.get('发布时间', '')))
        self.count_label.setText(f"共 {len(articles)} 条记录")
    
    def _on_search(self, text):
        self._apply_filters()
    
    def _on_filter_changed(self, account):
        self._apply_filters()
    
    def _apply_filters(self):
        """
        应用筛选条件
        
        根据搜索关键词和公众号筛选条件过滤文章列表。
        """
        search_text = self.search_input.text().strip().lower()
        account_filter = self.account_filter.currentText()
        # 组合筛选条件：公众号匹配 AND 标题包含关键词
        filtered = [a for a in self.articles if (account_filter == "全部" or a.get('公众号', '') == account_filter) and (not search_text or search_text in a.get('标题', '').lower())]
        self._display_articles(filtered)
    
    def _on_selection_changed(self):
        """表格选择变化时的处理（保留用于未来扩展）"""
        pass
    
    def _on_table_double_clicked(self, index):
        """双击表格行打开全屏预览"""
        self._on_fullscreen_preview()
    
    def _on_fullscreen_preview(self):
        """
        打开全屏预览对话框
        
        创建或重用预览对话框，显示当前选中文章的详细内容，
        支持在对话框中切换上一篇/下一篇文章。
        """
        row = self.data_table.currentRow()
        if row < 0:
            return
        
        # 获取当前过滤后的文章列表
        filtered = self._get_filtered_articles()
        if not filtered:
            return
        
        # 创建或重用预览对话框
        if self.preview_dialog is None:
            self.preview_dialog = ArticlePreviewDialog(self.window())
            self.preview_dialog.article_changed.connect(self._on_preview_article_changed)
        
        # 设置文章列表和当前索引
        self.preview_dialog.set_articles(filtered, row)
        self.preview_dialog.exec()
    
    def _on_preview_article_changed(self, index):
        """预览对话框中切换文章时同步选中表格行"""
        if 0 <= index < self.data_table.rowCount():
            self.data_table.selectRow(index)
    
    def _get_filtered_articles(self):
        """获取当前过滤后的文章列表"""
        search_text = self.search_input.text().strip().lower()
        account_filter = self.account_filter.currentText()
        return [a for a in self.articles if (account_filter == "全部" or a.get('公众号', '') == account_filter) and (not search_text or search_text in a.get('标题', '').lower())]
    
    def _on_context_menu(self, pos):
        """显示右键菜单"""
        # 获取点击位置的行
        item = self.data_table.itemAt(pos)
        if item is None:
            return
        
        row = item.row()
        if row < 0:
            return
        
        # 获取当前过滤后的文章列表
        filtered = self._get_filtered_articles()
        if row >= len(filtered):
            return
        
        article = filtered[row]
        link = article.get('链接', '')
        
        # 创建右键菜单
        menu = QMenu(self)
        
        # 全屏预览
        preview_action = QAction("全屏预览", self)
        preview_action.triggered.connect(lambda: self._preview_article_at_row(row))
        menu.addAction(preview_action)
        
        # 在浏览器中打开
        if link:
            open_action = QAction("在浏览器中打开", self)
            open_action.triggered.connect(lambda: QDesktopServices.openUrl(QUrl(link)))
            menu.addAction(open_action)
        
        menu.addSeparator()
        
        # 图片提取
        if link:
            extract_action = QAction("图片提取", self)
            extract_action.triggered.connect(lambda: self._on_extract_images(link))
            menu.addAction(extract_action)
        
        # 显示菜单
        menu.exec(self.data_table.viewport().mapToGlobal(pos))
    
    def _preview_article_at_row(self, row):
        """预览指定行的文章"""
        self.data_table.selectRow(row)
        self._on_fullscreen_preview()
    
    def _on_extract_images(self, link):
        """发送图片提取请求"""
        self.extract_images_requested.emit(link)
    
    def _on_export_all(self):
        if not self.articles:
            InfoBar.warning(title="提示", content="没有数据可导出", parent=self, position=InfoBarPosition.TOP, duration=2000)
            return
        file_path, _ = QFileDialog.getSaveFileName(self, "导出文件", "", "CSV文件 (*.csv)")
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8-sig', newline='') as f:
                    if self.articles:
                        writer = csv.DictWriter(f, fieldnames=self.articles[0].keys())
                        writer.writeheader()
                        writer.writerows(self.articles)
                InfoBar.success(title="导出成功", content=f"数据已导出到 {file_path}", parent=self, position=InfoBarPosition.TOP, duration=3000)
            except Exception as e:
                InfoBar.error(title="导出失败", content=str(e), parent=self, position=InfoBarPosition.TOP, duration=3000)
    
    def _on_open_folder(self):
        # 导入默认输出目录
        from gui.utils import DEFAULT_OUTPUT_DIR
        results_dir = os.path.abspath(DEFAULT_OUTPUT_DIR)
        if not os.path.exists(results_dir):
            os.makedirs(results_dir)
        QDesktopServices.openUrl(QUrl.fromLocalFile(results_dir))
    
    def load_articles_data(self, articles, source_info="爬取结果", temp_file_path=None):
        """直接加载文章数据（从爬取结果）
        
        Args:
            articles: 文章列表，每篇文章是包含 name/title/link/publish_time/content 的字典
            source_info: 数据来源描述
            temp_file_path: 临时文件路径（爬取时自动保存的文件，用户放弃时需要删除）
        """
        # 转换数据格式以与 CSV 格式一致
        self.articles = []
        accounts = set()
        for article in articles:
            row = {
                '公众号': article.get('name', ''),
                '标题': article.get('title', ''),
                '发布时间': article.get('publish_time', ''),
                '链接': article.get('link', ''),
                '内容': article.get('content', '')
            }
            self.articles.append(row)
            if row['公众号']:
                accounts.add(row['公众号'])
        
        # 更新状态
        self.current_file = None
        self.is_unsaved = True
        self.source_info = source_info
        self.temp_file_path = temp_file_path  # 保存临时文件路径
        
        # 更新公众号过滤器
        self.account_filter.clear()
        self.account_filter.addItem("全部")
        for account in sorted(accounts):
            self.account_filter.addItem(account)
        
        # 显示数据
        self._display_articles(self.articles)
        
        # 显示来源信息和操作按钮
        self.source_label.setText(f"数据来源: {source_info} | 共 {len(self.articles)} 条记录 (未保存)")
        self.source_card.show()
        self.save_btn.show()
        self.discard_btn.show()
        
        # 清空文件输入框
        self.file_input.clear()
        
        InfoBar.success(
            title="数据已加载", 
            content=f"{source_info} - 共 {len(self.articles)} 条记录", 
            parent=self, 
            position=InfoBarPosition.TOP, 
            duration=3000
        )
    
    def _on_save_results(self):
        """
        保存爬取结果
        
        支持多种文件格式导出：CSV、JSON、Excel、Markdown、HTML。
        保存成功后会删除临时文件，避免重复。
        """
        if not self.articles:
            InfoBar.warning(title="提示", content="没有数据可保存", parent=self, position=InfoBarPosition.TOP, duration=2000)
            return
        
        # 生成默认文件名 - 根据公众号数量生成不同的文件名
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 获取所有公众号名称
        accounts = set()
        for article in self.articles:
            account_name = article.get('公众号', '')
            if account_name:
                accounts.add(account_name)
        
        if len(accounts) == 1:
            # 单个公众号：公众号名_时间戳
            account_name = list(accounts)[0]
            # 清理文件名中的非法字符
            safe_name = "".join(c for c in account_name if c not in r'\/:*?"<>|')
            base_name = f"{safe_name}_{timestamp}"
        elif len(accounts) > 1:
            # 多个公众号：批量爬取_N个公众号_时间戳
            base_name = f"批量爬取_{len(accounts)}个公众号_{timestamp}"
        else:
            # 无公众号信息时使用默认名称
            base_name = f"爬取结果_{timestamp}"
        
        # 构建文件过滤器字符串
        filter_parts = []
        for fmt_key, (fmt_name, fmt_ext) in SUPPORTED_FORMATS.items():
            filter_parts.append(f"{fmt_name} (*{fmt_ext})")
        filter_str = ";;".join(filter_parts)
        
        # 默认使用CSV格式，保存到用户目录下的 WeChatSpider 文件夹
        default_name = os.path.join(DEFAULT_OUTPUT_DIR, f"{base_name}.csv")
        
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self, "保存结果", default_name, filter_str
        )
        
        if file_path:
            try:
                # 确保目录存在
                os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
                
                # 根据文件扩展名确定保存格式
                _, ext = os.path.splitext(file_path)
                ext = ext.lower()
                
                if ext == '.csv':
                    self._save_as_csv(file_path)
                elif ext == '.json':
                    self._save_as_json(file_path)
                elif ext == '.xlsx':
                    self._save_as_excel(file_path)
                elif ext == '.md':
                    self._save_as_markdown(file_path)
                elif ext == '.html':
                    self._save_as_html(file_path)
                else:
                    # 默认保存为CSV
                    if not ext:
                        file_path += '.csv'
                    self._save_as_csv(file_path)
                
                # 保存成功后，删除临时文件（避免重复文件）
                self._delete_temp_file()
                
                # 更新状态
                self.current_file = file_path
                self.is_unsaved = False
                self.temp_file_path = None  # 清除临时文件路径
                self.source_label.setText(f"数据来源: {self.source_info} | 已保存到 {os.path.basename(file_path)}")
                self.save_btn.hide()
                self.discard_btn.hide()
                
                # 刷新最近文件列表
                self._update_recent_files()
                
                InfoBar.success(
                    title="保存成功",
                    content=f"数据已保存到 {file_path}",
                    parent=self,
                    position=InfoBarPosition.TOP,
                    duration=3000
                )
            except Exception as e:
                InfoBar.error(
                    title="保存失败",
                    content=str(e),
                    parent=self,
                    position=InfoBarPosition.TOP,
                    duration=3000
                )
    
    def _save_as_csv(self, file_path):
        """
        保存为 CSV 格式
        
        使用 utf-8-sig 编码，确保 Excel 能正确识别中文。
        
        Args:
            file_path: 保存路径
        """
        with open(file_path, 'w', encoding='utf-8-sig', newline='') as f:
            if self.articles:
                writer = csv.DictWriter(f, fieldnames=self.articles[0].keys())
                writer.writeheader()
                writer.writerows(self.articles)
    
    def _save_as_json(self, file_path):
        """保存为JSON格式"""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.articles, f, ensure_ascii=False, indent=2)
    
    def _save_as_excel(self, file_path):
        """保存为Excel格式"""
        try:
            import pandas as pd
            df = pd.DataFrame(self.articles)
            df.to_excel(file_path, index=False, engine='openpyxl')
        except ImportError:
            raise ImportError("保存Excel格式需要安装 pandas 和 openpyxl 库。\n请运行: pip install pandas openpyxl")
    
    def _save_as_markdown(self, file_path):
        """
        保存为 Markdown 格式
        
        生成结构化的 Markdown 文档，包含文章列表和内容。
        
        Args:
            file_path: 保存路径
        """
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("# 微信公众号文章爬取结果\n\n")
            f.write(f"共 {len(self.articles)} 篇文章\n\n")
            f.write("---\n\n")
            
            for i, article in enumerate(self.articles, 1):
                f.write(f"## {i}. {article.get('标题', '无标题')}\n\n")
                f.write(f"- **公众号**: {article.get('公众号', '未知')}\n")
                f.write(f"- **发布时间**: {article.get('发布时间', '未知')}\n")
                link = article.get('链接', '')
                if link:
                    f.write(f"- **链接**: [{link}]({link})\n")
                f.write("\n")
                
                content = article.get('内容', '')
                if content:
                    f.write("### 内容\n\n")
                    f.write(content)
                    f.write("\n\n")
                
                f.write("---\n\n")
    
    def _save_as_html(self, file_path):
        """保存为HTML格式 - 单篇文章显示，支持左右切换"""
        # 准备文章数据为JSON格式嵌入HTML
        articles_json = []
        for i, article in enumerate(self.articles):
            articles_json.append({
                'index': i + 1,
                'title': self._escape_html(article.get('标题', '无标题')),
                'account': self._escape_html(article.get('公众号', '未知')),
                'pub_time': self._escape_html(article.get('发布时间', '未知')),
                'link': article.get('链接', ''),
                'content': self._markdown_to_html(article.get('内容', ''))
            })
        
        # 将文章数据转换为JSON字符串
        import json
        articles_data = json.dumps(articles_json, ensure_ascii=False)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>微信公众号文章爬取结果</title>
    <style>
        * { box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            margin: 0;
            padding: 0;
            background: #f5f5f5;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }
        
        /* 顶部导航栏 */
        .header {
            background: linear-gradient(135deg, #07c160 0%, #05a14e 100%);
            color: white;
            padding: 15px 20px;
            position: sticky;
            top: 0;
            z-index: 100;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
        }
        .header h1 {
            margin: 0 0 10px 0;
            font-size: 20px;
            font-weight: 600;
        }
        .nav-controls {
            display: flex;
            align-items: center;
            gap: 15px;
            flex-wrap: wrap;
        }
        .nav-btn {
            background: rgba(255,255,255,0.2);
            border: none;
            color: white;
            padding: 8px 20px;
            border-radius: 20px;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.3s;
            display: flex;
            align-items: center;
            gap: 5px;
        }
        .nav-btn:hover:not(:disabled) {
            background: rgba(255,255,255,0.3);
            transform: translateY(-1px);
        }
        .nav-btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        .page-info {
            background: rgba(255,255,255,0.2);
            padding: 8px 15px;
            border-radius: 20px;
            font-size: 14px;
        }
        .article-select {
            padding: 8px 12px;
            border-radius: 20px;
            border: none;
            background: rgba(255,255,255,0.9);
            color: #333;
            font-size: 14px;
            max-width: 300px;
            cursor: pointer;
        }
        
        /* 文章容器 */
        .article-container {
            flex: 1;
            max-width: 900px;
            margin: 20px auto;
            padding: 0 20px;
            width: 100%;
        }
        .article {
            background: white;
            border-radius: 12px;
            padding: 30px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
            animation: fadeIn 0.3s ease;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .article h2 {
            color: #07c160;
            margin: 0 0 20px 0;
            font-size: 24px;
            line-height: 1.4;
        }
        .meta {
            color: #666;
            font-size: 14px;
            margin-bottom: 25px;
            padding-bottom: 15px;
            border-bottom: 1px solid #eee;
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
        }
        .meta-item {
            display: flex;
            align-items: center;
            gap: 5px;
        }
        .content {
            line-height: 1.9;
            color: #333;
            font-size: 16px;
        }
        .content img {
            max-width: 100%;
            height: auto;
            border-radius: 8px;
            margin: 15px 0;
        }
        .content p {
            margin: 0 0 15px 0;
        }
        .content a {
            color: #07c160;
            text-decoration: none;
        }
        .content a:hover {
            text-decoration: underline;
        }
        .no-content {
            color: #999;
            font-style: italic;
            text-align: center;
            padding: 40px;
        }
        
        /* 底部导航 */
        .footer-nav {
            background: white;
            padding: 15px 20px;
            display: flex;
            justify-content: center;
            gap: 20px;
            box-shadow: 0 -2px 10px rgba(0,0,0,0.05);
        }
        .footer-btn {
            background: #07c160;
            border: none;
            color: white;
            padding: 12px 30px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 15px;
            transition: all 0.3s;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .footer-btn:hover:not(:disabled) {
            background: #05a14e;
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(7,193,96,0.3);
        }
        .footer-btn:disabled {
            background: #ccc;
            cursor: not-allowed;
        }
        
        /* 键盘快捷键提示 */
        .keyboard-hint {
            text-align: center;
            color: #999;
            font-size: 12px;
            padding: 10px;
            background: #f9f9f9;
        }
        .keyboard-hint kbd {
            background: #eee;
            padding: 2px 8px;
            border-radius: 4px;
            border: 1px solid #ddd;
            font-family: monospace;
        }
        
        /* 响应式设计 */
        @media (max-width: 768px) {
            .header h1 { font-size: 18px; }
            .nav-controls { gap: 10px; }
            .nav-btn { padding: 6px 15px; font-size: 13px; }
            .article { padding: 20px; }
            .article h2 { font-size: 20px; }
            .content { font-size: 15px; }
            .article-select { max-width: 200px; }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>📚 微信公众号文章爬取结果</h1>
        <div class="nav-controls">
            <button class="nav-btn" id="prevBtn" onclick="prevArticle()">
                ◀ 上一篇
            </button>
            <span class="page-info" id="pageInfo">1 / """ + str(len(self.articles)) + """</span>
            <button class="nav-btn" id="nextBtn" onclick="nextArticle()">
                下一篇 ▶
            </button>
            <select class="article-select" id="articleSelect" onchange="goToArticle(this.value)">
            </select>
        </div>
    </div>
    
    <div class="article-container">
        <div class="article" id="articleContent">
            <!-- 文章内容将通过JavaScript动态填充 -->
        </div>
    </div>
    
    <div class="footer-nav">
        <button class="footer-btn" id="footerPrevBtn" onclick="prevArticle()">
            ◀ 上一篇
        </button>
        <button class="footer-btn" id="footerNextBtn" onclick="nextArticle()">
            下一篇 ▶
        </button>
    </div>
    
    <div class="keyboard-hint">
        💡 快捷键: <kbd>←</kbd> 上一篇 | <kbd>→</kbd> 下一篇 | <kbd>Home</kbd> 第一篇 | <kbd>End</kbd> 最后一篇
    </div>

    <script>
        // 文章数据
        const articles = """ + articles_data + """;
        let currentIndex = 0;
        
        // 初始化
        function init() {
            // 填充下拉选择框
            const select = document.getElementById('articleSelect');
            articles.forEach((article, index) => {
                const option = document.createElement('option');
                option.value = index;
                option.textContent = `${article.index}. ${article.title.substring(0, 30)}${article.title.length > 30 ? '...' : ''}`;
                select.appendChild(option);
            });
            
            // 显示第一篇文章
            showArticle(0);
        }
        
        // 显示指定文章
        function showArticle(index) {
            if (index < 0 || index >= articles.length) return;
            
            currentIndex = index;
            const article = articles[index];
            
            // 更新文章内容
            const container = document.getElementById('articleContent');
            let linkHtml = '';
            if (article.link) {
                linkHtml = `<span class="meta-item">🔗 <a href="${article.link}" target="_blank">原文链接</a></span>`;
            }
            
            let contentHtml = article.content || '<div class="no-content">暂无内容</div>';
            
            container.innerHTML = `
                <h2>${article.index}. ${article.title}</h2>
                <div class="meta">
                    <span class="meta-item">📱 公众号: ${article.account}</span>
                    <span class="meta-item">📅 发布时间: ${article.pub_time}</span>
                    ${linkHtml}
                </div>
                <div class="content">${contentHtml}</div>
            `;
            
            // 更新页码信息
            document.getElementById('pageInfo').textContent = `${index + 1} / ${articles.length}`;
            
            // 更新下拉选择框
            document.getElementById('articleSelect').value = index;
            
            // 更新按钮状态
            updateButtons();
            
            // 滚动到顶部
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }
        
        // 更新按钮状态
        function updateButtons() {
            const isFirst = currentIndex === 0;
            const isLast = currentIndex === articles.length - 1;
            
            document.getElementById('prevBtn').disabled = isFirst;
            document.getElementById('nextBtn').disabled = isLast;
            document.getElementById('footerPrevBtn').disabled = isFirst;
            document.getElementById('footerNextBtn').disabled = isLast;
        }
        
        // 上一篇
        function prevArticle() {
            if (currentIndex > 0) {
                showArticle(currentIndex - 1);
            }
        }
        
        // 下一篇
        function nextArticle() {
            if (currentIndex < articles.length - 1) {
                showArticle(currentIndex + 1);
            }
        }
        
        // 跳转到指定文章
        function goToArticle(index) {
            showArticle(parseInt(index));
        }
        
        // 键盘快捷键
        document.addEventListener('keydown', function(e) {
            // 如果焦点在输入框或选择框中，不处理快捷键
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT' || e.target.tagName === 'TEXTAREA') {
                return;
            }
            
            switch(e.key) {
                case 'ArrowLeft':
                    prevArticle();
                    e.preventDefault();
                    break;
                case 'ArrowRight':
                    nextArticle();
                    e.preventDefault();
                    break;
                case 'Home':
                    showArticle(0);
                    e.preventDefault();
                    break;
                case 'End':
                    showArticle(articles.length - 1);
                    e.preventDefault();
                    break;
            }
        });
        
        // 页面加载完成后初始化
        document.addEventListener('DOMContentLoaded', init);
    </script>
</body>
</html>
""")
    
    def _escape_html(self, text):
        """转义HTML特殊字符"""
        if not text:
            return ''
        return (str(text)
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#39;'))
    
    def _markdown_to_html(self, md_text):
        """简单的Markdown到HTML转换"""
        if not md_text:
            return ''
        
        # 尝试使用markdown库
        try:
            import markdown
            return markdown.markdown(md_text, extensions=['tables', 'fenced_code'])
        except ImportError:
            # 如果没有markdown库，进行简单转换
            html = self._escape_html(md_text)
            # 转换换行
            html = html.replace('\n\n', '</p><p>')
            html = html.replace('\n', '<br>')
            # 转换图片
            import re
            html = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', r'<img src="\2" alt="\1">', html)
            # 转换链接
            html = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', html)
            return f'<p>{html}</p>'
    
    def _on_discard_data(self):
        """放弃未保存的数据"""
        if not self.is_unsaved:
            return
        
        # 显示确认对话框
        msg_box = MessageBox(
            "确认放弃数据",
            f"确定要放弃这 {len(self.articles)} 条爬取结果吗？\n\n此操作不可撤销，数据将永久丢失。",
            self.window()
        )
        msg_box.yesButton.setText("放弃数据")
        msg_box.cancelButton.setText("取消")
        
        if msg_box.exec():
            # 用户确认放弃 - 删除临时文件
            self._delete_temp_file()
            # 清除数据
            self._clear_unsaved_data()
            InfoBar.info(
                title="已放弃",
                content="爬取数据已丢弃，临时文件已删除",
                parent=self,
                position=InfoBarPosition.TOP,
                duration=2000
            )
            # 发射信号通知主窗口
            self.data_discarded.emit()
    
    def _delete_temp_file(self):
        """删除临时文件"""
        if self.temp_file_path and os.path.exists(self.temp_file_path):
            try:
                os.remove(self.temp_file_path)
                # 刷新最近文件列表
                self._update_recent_files()
            except Exception as e:
                # 删除失败时记录错误但不阻止操作
                print(f"删除临时文件失败: {e}")
    
    def _clear_unsaved_data(self):
        """
        清除未保存的数据
        
        重置页面状态，清空所有数据和界面显示。
        """
        self.articles = []
        self.is_unsaved = False
        self.source_info = ""
        self.current_file = None
        self.temp_file_path = None  # 清除临时文件路径
        
        # 清空表格
        self.data_table.setRowCount(0)
        self.count_label.setText("共 0 条记录")
        
        # 清空过滤器
        self.account_filter.clear()
        self.account_filter.addItem("全部")
        
        # 隐藏来源卡片和按钮
        self.source_card.hide()
        self.save_btn.hide()
        self.discard_btn.hide()
        
        # 重置来源标签
        self.source_label.setText("数据来源: 未加载")
    
    def has_unsaved_data(self):
        """检查是否有未保存的数据"""
        return self.is_unsaved and len(self.articles) > 0
