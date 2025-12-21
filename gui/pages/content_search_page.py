#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
内容搜索页面模块

提供对爬取结果的内容搜索功能，支持通配符模式匹配。

主要功能：
    - 加载 CSV/JSON/Markdown 格式的数据文件
    - 通配符搜索（* 匹配任意字符，? 匹配单个字符）
    - 预设常用网盘链接搜索模式
    - 搜索结果高亮显示
    - 结果导出（TXT/CSV/JSON）

使用场景：
    - 从爬取的文章中提取网盘链接
    - 搜索特定格式的内容（如邮箱、电话等）
    - 批量提取符合模式的文本

技术特点：
    - 通配符转正则表达式
    - URL 模式特殊处理（限制匹配字符范围）
    - 智能 URL 清理（移除末尾非法字符）
    - 紧凑单屏布局设计
"""

import re
import os
import csv
import json
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QHeaderView,
    QFileDialog, QTableWidgetItem, QAbstractItemView, QMenu,
    QSplitter
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices, QAction

from qfluentwidgets import (
    TitleLabel, BodyLabel, CardWidget,
    PrimaryPushButton, PushButton, LineEdit, ComboBox,
    InfoBar, InfoBarPosition, FluentIcon,
    CaptionLabel, ToolTipFilter, ToolTipPosition
)
from qfluentwidgets import TableWidget as FluentTable

from ..styles import COLORS


def wildcard_to_regex(pattern, is_url_pattern=False):
    """
    将通配符模式转换为正则表达式
    
    支持的通配符：
        - * (星号): 匹配任意数量的任意字符
        - ? (问号): 匹配单个任意字符
    
    特殊处理：
        - 自动转义正则表达式特殊字符
        - URL 模式下限制匹配字符范围（只匹配 URL 合法字符）
    
    Args:
        pattern: 通配符模式字符串
        is_url_pattern: 是否为 URL 模式，如果是则限制匹配字符范围
        
    Returns:
        re.Pattern: 编译后的正则表达式对象（忽略大小写）
    
    Examples:
        >>> regex = wildcard_to_regex("https://pan.quark.cn/s/*", is_url_pattern=True)
        >>> regex.search("链接: https://pan.quark.cn/s/abc123")
    """
    regex_pattern = ""
    for char in pattern:
        if char == '*':
            if is_url_pattern:
                # URL模式：只匹配URL合法字符（不包括空格、换行、*、中文等）
                regex_pattern += r'[A-Za-z0-9_\-\.~:/?#\[\]@!$&\'()+,;=%]*'
            else:
                regex_pattern += '.*'
        elif char == '?':
            if is_url_pattern:
                regex_pattern += r'[A-Za-z0-9_\-\.~:/?#\[\]@!$&\'()+,;=%]'
            else:
                regex_pattern += '.'
        elif char in r'\[](){}|^$+.':
            regex_pattern += '\\' + char
        else:
            regex_pattern += char
    
    return re.compile(regex_pattern, re.IGNORECASE)


def extract_urls_from_text(text, url_pattern_regex):
    """
    从文本中精确提取 URL
    
    使用正则表达式匹配文本中的 URL，并进行清理和去重。
    
    Args:
        text: 要搜索的文本
        url_pattern_regex: URL 匹配的正则表达式
        
    Returns:
        list: 匹配到的 URL 列表（已去重、已清理）
    """
    matches = []
    for match in url_pattern_regex.finditer(text):
        url = match.group()
        # 清理URL末尾可能的非法字符
        url = clean_url(url)
        if url and url not in matches:
            matches.append(url)
    return matches


def clean_url(url):
    """
    清理 URL，移除末尾的非法字符
    
    处理从文本中提取的 URL 可能包含的尾部垃圾字符，
    如中文标点、括号等。
    
    Args:
        url: 原始 URL 字符串
        
    Returns:
        str: 清理后的 URL
    """
    if not url:
        return url
    
    # 移除末尾的常见非URL字符
    invalid_trailing = ['*', ')', ']', '>', '"', "'", '，', '。', '！', '？',
                        '、', '；', '：', '"', '"', ''', ''', '）', '】', '》',
                        '\n', '\r', '\t', ' ']
    
    changed = True
    while changed and url:
        changed = False
        for char in invalid_trailing:
            if url.endswith(char):
                url = url[:-1]
                changed = True
                break
    
    return url


class ContentSearchPage(QWidget):
    """
    内容搜索页面
    
    提供对爬取结果的内容搜索功能，支持通配符模式匹配。
    采用紧凑的单屏布局设计，无需滚动即可操作。
    
    界面布局：
        ┌─────────────────────────────────────────┐
        │  标题 + 帮助按钮                         │
        ├─────────────────────────────────────────┤
        │  数据源选择 | 浏览 | 状态                │
        │  搜索输入框                    | 搜索    │
        │  快捷按钮: 夸克 百度 阿里 蓝奏 115 迅雷  │
        ├─────────────────────────────────────────┤
        │  搜索结果: X 条匹配              导出    │
        ├─────────────────────────────────────────┤
        │  结果表格（公众号 | 标题 | 匹配内容 | 时间）│
        └─────────────────────────────────────────┘
    
    Attributes:
        articles: 加载的文章数据列表
        search_results: 搜索结果列表
        current_file: 当前加载的文件路径
    """
    
    def __init__(self, parent=None):
        """
        初始化内容搜索页面
        
        Args:
            parent: 父控件
        """
        super().__init__(parent)
        self.articles = []
        self.search_results = []
        self.current_file = None
        self.setObjectName("contentSearchPage")
        self._setup_ui()
        self._apply_dark_background()
    
    def _apply_dark_background(self):
        """
        应用暗黑背景样式
        
        设置页面背景色为暗黑主题色。
        """
        self.setStyleSheet("background-color: #1a1a1a;")
    
    def _setup_ui(self):
        """
        构建页面界面
        
        创建紧凑的单屏布局，包括：
        - 标题和帮助按钮
        - 数据源选择和搜索输入
        - 快捷搜索按钮
        - 结果统计和导出
        - 搜索结果表格
        """
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(10)
        
        # 标题行 + 帮助提示
        title_layout = QHBoxLayout()
        title_label = TitleLabel("内容搜索")
        title_layout.addWidget(title_label)
        
        # 帮助提示按钮
        help_btn = PushButton("?")
        help_btn.setFixedSize(38, 28)
        help_btn.setToolTip(
            "通配符搜索说明：\n"
            "• * (星号) - 匹配任意数量的任意字符\n"
            "• ? (问号) - 匹配单个任意字符\n\n"
            "示例：\n"
            "• https://pan.quark.cn/s/* - 搜索夸克网盘链接\n"
            "• https://pan.baidu.com/* - 搜索百度网盘链接"
        )
        help_btn.installEventFilter(ToolTipFilter(help_btn, 300, ToolTipPosition.BOTTOM))
        title_layout.addWidget(help_btn)
        title_layout.addStretch()
        layout.addLayout(title_layout)
        
        # 数据源 + 搜索条件（合并为一个紧凑卡片）
        control_card = CardWidget()
        control_layout = QVBoxLayout(control_card)
        control_layout.setContentsMargins(15, 12, 15, 12)
        control_layout.setSpacing(8)
        
        # 第一行：数据源选择
        source_layout = QHBoxLayout()
        source_layout.setSpacing(8)
        
        source_label = BodyLabel("数据源:")
        source_label.setFixedWidth(55)
        source_layout.addWidget(source_label)
        
        self.recent_combo = ComboBox()
        self.recent_combo.setMinimumWidth(200)
        self._update_recent_files()
        self.recent_combo.currentIndexChanged.connect(self._on_combo_changed)
        source_layout.addWidget(self.recent_combo)
        
        browse_btn = PushButton("浏览")
        browse_btn.setFixedWidth(60)
        browse_btn.clicked.connect(self._on_browse_file)
        source_layout.addWidget(browse_btn)
        
        source_layout.addSpacing(10)
        
        # 数据状态标签
        self.data_status_label = CaptionLabel("未加载")
        self.data_status_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        source_layout.addWidget(self.data_status_label)
        source_layout.addStretch()
        
        control_layout.addLayout(source_layout)
        
        # 第二行：搜索输入
        search_layout = QHBoxLayout()
        search_layout.setSpacing(8)
        
        search_label = BodyLabel("搜索:")
        search_label.setFixedWidth(55)
        search_layout.addWidget(search_label)
        
        self.search_input = LineEdit()
        self.search_input.setPlaceholderText("输入搜索模式，支持通配符 * 和 ?  例如: https://pan.quark.cn/s/*")
        self.search_input.returnPressed.connect(self._on_search)
        search_layout.addWidget(self.search_input)
        
        search_btn = PrimaryPushButton("搜索")
        search_btn.setFixedWidth(70)
        search_btn.clicked.connect(self._on_search)
        search_layout.addWidget(search_btn)
        
        control_layout.addLayout(search_layout)
        
        # 第三行：常用模式按钮
        preset_layout = QHBoxLayout()
        preset_layout.setSpacing(6)
        
        preset_label = BodyLabel("快捷:")
        preset_label.setFixedWidth(55)
        preset_layout.addWidget(preset_label)
        
        presets = [
            ("夸克", "https://pan.quark.cn/s/*"),
            ("百度", "https://pan.baidu.com/*"),
            ("阿里", "https://*aliyundrive.com/*"),
            ("蓝奏", "https://*lanzou*.com/*"),
            ("115", "https://115.com/s/*"),
            ("迅雷", "https://pan.xunlei.com/s/*"),
        ]
        
        for name, pattern in presets:
            btn = PushButton(name)
            btn.setFixedWidth(55)
            btn.clicked.connect(lambda checked, p=pattern: self._set_search_pattern(p))
            preset_layout.addWidget(btn)
        
        preset_layout.addStretch()
        control_layout.addLayout(preset_layout)
        
        layout.addWidget(control_card)
        
        # 搜索结果统计行
        result_header = QHBoxLayout()
        result_header.setSpacing(10)
        
        self.result_count_label = BodyLabel("搜索结果: 0 条匹配")
        result_header.addWidget(self.result_count_label)
        result_header.addStretch()
        
        # 导出按钮
        self.export_btn = PushButton("导出")
        self.export_btn.setFixedWidth(60)
        self.export_btn.clicked.connect(self._on_export_results)
        self.export_btn.setEnabled(False)
        result_header.addWidget(self.export_btn)
        
        layout.addLayout(result_header)
        
        # 搜索结果表格（占据剩余空间）
        self.result_table = FluentTable()
        self.result_table.setColumnCount(4)
        self.result_table.setHorizontalHeaderLabels(["公众号", "标题", "匹配内容", "发布时间"])
        self.result_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.result_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        self.result_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.result_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.result_table.setColumnWidth(1, 180)
        self.result_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.result_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.result_table.customContextMenuRequested.connect(self._on_context_menu)
        self.result_table.doubleClicked.connect(self._on_table_double_clicked)
        layout.addWidget(self.result_table, 1)  # stretch=1 让表格占据剩余空间
    
    def _update_recent_files(self):
        """
        更新最近文件下拉列表
        
        递归扫描输出目录中的数据文件（CSV/JSON/MD），
        按修改时间倒序排列，显示最近的30个文件。
        """
        self.recent_combo.clear()
        # 导入默认输出目录
        from gui.utils import DEFAULT_OUTPUT_DIR
        
        self.recent_combo.addItem("选择文件...")
        results_dir = DEFAULT_OUTPUT_DIR  # 使用用户文档目录
        if os.path.exists(results_dir):
            files = []
            self._scan_files_recursive(results_dir, files)
            
            files.sort(key=lambda x: x[2], reverse=True)
            
            for name, path, _ in files[:30]:
                # 显示相对路径
                rel_path = os.path.relpath(path, results_dir)
                self.recent_combo.addItem(rel_path, userData=path)
    
    def _scan_files_recursive(self, directory, files):
        """
        递归扫描目录中的数据文件
        
        Args:
            directory: 要扫描的目录路径
            files: 结果列表，元素为 (文件名, 完整路径, 修改时间)
        """
        try:
            for f in os.listdir(directory):
                path = os.path.join(directory, f)
                if os.path.isdir(path):
                    self._scan_files_recursive(path, files)
                elif f.endswith('.csv') or f.endswith('.json') or f.endswith('.md'):
                    files.append((f, path, os.path.getmtime(path)))
        except PermissionError:
            pass
    
    def _on_combo_changed(self, index):
        """
        下拉框选择变化时自动加载文件
        
        Args:
            index: 选中项索引
        """
        if index > 0:
            file_path = self.recent_combo.currentData()
            if file_path and os.path.exists(file_path):
                self._load_data_file(file_path)
    
    def _on_browse_file(self):
        """浏览文件"""
        # 导入默认输出目录
        from gui.utils import DEFAULT_OUTPUT_DIR
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择数据文件", DEFAULT_OUTPUT_DIR,
            "数据文件 (*.csv *.json *.md);;CSV文件 (*.csv);;JSON文件 (*.json);;Markdown文件 (*.md)"
        )
        if file_path:
            self._load_data_file(file_path)
    
    def _load_data_file(self, file_path):
        """加载数据文件"""
        try:
            self.articles = []
            
            if file_path.endswith('.csv'):
                self._load_csv(file_path)
            elif file_path.endswith('.json'):
                self._load_json(file_path)
            elif file_path.endswith('.md'):
                self._load_markdown(file_path)
            else:
                raise ValueError("不支持的文件格式，支持: CSV, JSON, MD")
            
            self.current_file = file_path
            self.data_status_label.setText(f"已加载 {len(self.articles)} 篇")
            self.data_status_label.setStyleSheet(f"color: {COLORS['success']};")
            
            # 清空搜索结果
            self.search_results = []
            self.result_table.setRowCount(0)
            self.result_count_label.setText("搜索结果: 0 条匹配")
            self.export_btn.setEnabled(False)
            
            InfoBar.success(
                title="加载成功", 
                content=f"成功加载 {len(self.articles)} 篇文章", 
                parent=self, 
                position=InfoBarPosition.TOP, 
                duration=2000
            )
        except Exception as e:
            self.data_status_label.setText("加载失败")
            self.data_status_label.setStyleSheet(f"color: {COLORS['error']};")
            InfoBar.error(
                title="加载失败", 
                content=str(e), 
                parent=self, 
                position=InfoBarPosition.TOP, 
                duration=3000
            )
    
    def _load_csv(self, file_path):
        """加载CSV文件"""
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.articles.append(row)
    
    def _load_json(self, file_path):
        """加载JSON文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                self.articles = data
            else:
                raise ValueError("JSON文件格式不正确，应为文章列表")
    
    def _load_markdown(self, file_path):
        """
        加载 Markdown 文件
        
        将整个 MD 文件作为一篇文章处理。
        
        Args:
            file_path: Markdown 文件路径
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 将整个MD文件作为一篇文章处理
        filename = os.path.basename(file_path)
        title = os.path.splitext(filename)[0]
        
        self.articles.append({
            '公众号': '',
            '标题': title,
            '内容': content,
            '发布时间': '',
            '链接': ''
        })
    
    def _set_search_pattern(self, pattern):
        """设置搜索模式并自动搜索"""
        self.search_input.setText(pattern)
        if self.articles:
            self._on_search()
        else:
            self.search_input.setFocus()
    
    def _on_search(self):
        """执行搜索"""
        if not self.articles:
            InfoBar.warning(
                title="提示",
                content="请先加载数据文件",
                parent=self,
                position=InfoBarPosition.TOP,
                duration=2000
            )
            return
        
        pattern = self.search_input.text().strip()
        if not pattern:
            InfoBar.warning(
                title="提示",
                content="请输入搜索模式",
                parent=self,
                position=InfoBarPosition.TOP,
                duration=2000
            )
            return
        
        try:
            # 判断是否为URL模式
            is_url_pattern = pattern.startswith('http://') or pattern.startswith('https://')
            regex = wildcard_to_regex(pattern, is_url_pattern)
            
            self.search_results = []
            for article in self.articles:
                content = article.get('内容', '') or article.get('content', '')
                if not content:
                    continue
                
                if is_url_pattern:
                    # URL模式：使用专门的URL提取函数
                    url_matches = extract_urls_from_text(content, regex)
                    if url_matches:
                        match_contexts = []
                        for url in url_matches:
                            match_contexts.append({
                                'match': url,
                                'context': url
                            })
                        
                        self.search_results.append({
                            'article': article,
                            'matches': match_contexts,
                            'match_count': len(url_matches)
                        })
                else:
                    # 普通模式
                    matches = regex.findall(content)
                    if matches:
                        match_contexts = []
                        for match in regex.finditer(content):
                            match_contexts.append({
                                'match': match.group(),
                                'context': match.group()
                            })
                        
                        self.search_results.append({
                            'article': article,
                            'matches': match_contexts,
                            'match_count': len(matches)
                        })
            
            self._display_results()
            
            if self.search_results:
                total_matches = sum(r['match_count'] for r in self.search_results)
                InfoBar.success(
                    title="搜索完成",
                    content=f"在 {len(self.search_results)} 篇文章中找到 {total_matches} 处匹配",
                    parent=self,
                    position=InfoBarPosition.TOP,
                    duration=2000
                )
            else:
                InfoBar.info(
                    title="搜索完成",
                    content="未找到匹配内容",
                    parent=self,
                    position=InfoBarPosition.TOP,
                    duration=2000
                )
                
        except Exception as e:
            InfoBar.error(
                title="搜索失败",
                content=str(e),
                parent=self,
                position=InfoBarPosition.TOP,
                duration=3000
            )
    
    def _display_results(self):
        """显示搜索结果"""
        self.result_table.setRowCount(0)
        
        total_matches = sum(r['match_count'] for r in self.search_results)
        self.result_count_label.setText(
            f"搜索结果: {len(self.search_results)} 篇文章, {total_matches} 处匹配"
        )
        
        row_index = 0
        for result in self.search_results:
            article = result['article']
            for match_info in result['matches']:
                self.result_table.insertRow(row_index)
                
                account = article.get('公众号', '') or article.get('name', '')
                self.result_table.setItem(row_index, 0, QTableWidgetItem(account))
                
                title = article.get('标题', '') or article.get('title', '')
                self.result_table.setItem(row_index, 1, QTableWidgetItem(title))
                
                self.result_table.setItem(row_index, 2, QTableWidgetItem(match_info['match']))
                
                pub_time = article.get('发布时间', '') or article.get('publish_time', '')
                self.result_table.setItem(row_index, 3, QTableWidgetItem(pub_time))
                
                row_index += 1
        
        self.export_btn.setEnabled(len(self.search_results) > 0)
    
    def _on_context_menu(self, pos):
        """右键菜单"""
        item = self.result_table.itemAt(pos)
        if item is None:
            return
        
        row = item.row()
        if row < 0:
            return
        
        match_item = self.result_table.item(row, 2)
        match_text = match_item.text() if match_item else ""
        
        menu = QMenu(self)
        
        copy_match_action = QAction("复制匹配内容", self)
        copy_match_action.triggered.connect(lambda: self._copy_to_clipboard(match_text))
        menu.addAction(copy_match_action)
        
        if match_text.startswith('http'):
            open_link_action = QAction("在浏览器中打开", self)
            open_link_action.triggered.connect(lambda: QDesktopServices.openUrl(QUrl(match_text)))
            menu.addAction(open_link_action)
        
        menu.addSeparator()
        
        copy_row_action = QAction("复制整行", self)
        copy_row_action.triggered.connect(lambda: self._copy_row(row))
        menu.addAction(copy_row_action)
        
        menu.exec(self.result_table.viewport().mapToGlobal(pos))
    
    def _copy_to_clipboard(self, text):
        """
        复制文本到剪贴板
        
        Args:
            text: 要复制的文本
        """
        from PyQt6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        InfoBar.success(
            title="已复制", 
            content="内容已复制到剪贴板", 
            parent=self, 
            position=InfoBarPosition.TOP, 
            duration=1500
        )
    
    def _copy_row(self, row):
        """复制整行数据"""
        cols = []
        for col in range(self.result_table.columnCount()):
            item = self.result_table.item(row, col)
            cols.append(item.text() if item else "")
        text = "\t".join(cols)
        self._copy_to_clipboard(text)
    
    def _on_table_double_clicked(self, index):
        """双击表格行"""
        row = index.row()
        col = index.column()
        
        if col == 2:
            item = self.result_table.item(row, 2)
            if item:
                text = item.text()
                if text.startswith('http'):
                    QDesktopServices.openUrl(QUrl(text))
                    return
        
        item = self.result_table.item(row, 2)
        if item:
            self._copy_to_clipboard(item.text())
    
    def _on_export_results(self):
        """导出搜索结果"""
        if not self.search_results:
            InfoBar.warning(
                title="提示", 
                content="没有可导出的结果", 
                parent=self, 
                position=InfoBarPosition.TOP, 
                duration=2000
            )
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pattern = self.search_input.text().strip()
        safe_pattern = "".join(c for c in pattern if c not in r'\/:*?"<>|')[:30]
        default_name = f"results/搜索结果_{safe_pattern}_{timestamp}.txt"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出搜索结果", default_name,
            "文本文件 (*.txt);;CSV文件 (*.csv);;JSON文件 (*.json)"
        )
        
        if not file_path:
            return
        
        try:
            os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
            
            _, ext = os.path.splitext(file_path)
            ext = ext.lower()
            
            if ext == '.csv':
                self._export_as_csv(file_path)
            elif ext == '.json':
                self._export_as_json(file_path)
            else:
                self._export_as_txt(file_path)
            
            InfoBar.success(
                title="导出成功", 
                content=f"结果已导出到 {os.path.basename(file_path)}", 
                parent=self, 
                position=InfoBarPosition.TOP, 
                duration=2000
            )
        except Exception as e:
            InfoBar.error(
                title="导出失败", 
                content=str(e), 
                parent=self, 
                position=InfoBarPosition.TOP, 
                duration=3000
            )
    
    def _export_as_csv(self, file_path):
        """
        导出为 CSV 格式
        
        Args:
            file_path: 保存路径
        """
        with open(file_path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['公众号', '标题', '匹配内容', '发布时间', '文章链接'])
            
            for result in self.search_results:
                article = result['article']
                account = article.get('公众号', '') or article.get('name', '')
                title = article.get('标题', '') or article.get('title', '')
                pub_time = article.get('发布时间', '') or article.get('publish_time', '')
                link = article.get('链接', '') or article.get('link', '')
                
                for match_info in result['matches']:
                    writer.writerow([account, title, match_info['match'], pub_time, link])
    
    def _export_as_json(self, file_path):
        """导出为JSON"""
        export_data = []
        for result in self.search_results:
            article = result['article']
            export_data.append({
                '公众号': article.get('公众号', '') or article.get('name', ''),
                '标题': article.get('标题', '') or article.get('title', ''),
                '发布时间': article.get('发布时间', '') or article.get('publish_time', ''),
                '链接': article.get('链接', '') or article.get('link', ''),
                '匹配内容': [m['match'] for m in result['matches']],
                '匹配数量': result['match_count']
            })
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
    
    def _export_as_txt(self, file_path):
        """导出为纯文本（仅匹配内容）"""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"搜索模式: {self.search_input.text()}\n")
            f.write(f"搜索时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"匹配文章数: {len(self.search_results)}\n")
            f.write("=" * 50 + "\n\n")
            
            unique_matches = set()
            for result in self.search_results:
                for match_info in result['matches']:
                    unique_matches.add(match_info['match'])
            
            f.write(f"唯一匹配内容 ({len(unique_matches)} 条):\n")
            f.write("-" * 30 + "\n")
            for match in sorted(unique_matches):
                f.write(f"{match}\n")
    