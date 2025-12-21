#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
设置页面模块

提供应用程序的全局设置界面，采用 Fluent Design 风格。

主要功能：
    - 爬取参数设置（页数、间隔、并发数、正文获取）
    - 存储设置（输出目录、缓存有效期）
    - 关于信息展示
    - 配置的保存和恢复

配置持久化：
    - 配置保存在 config.json 文件中
    - 支持恢复默认设置
    - 设置变更会通过信号通知其他页面

界面布局：
    - 爬取设置卡片
    - 存储设置卡片
    - 关于卡片
    - 保存/恢复按钮
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFrame
from PyQt6.QtCore import pyqtSignal, Qt
import json
import os

from qfluentwidgets import (
    ScrollArea, TitleLabel, BodyLabel, CaptionLabel, CardWidget,
    PrimaryPushButton, PushButton, LineEdit,
    SwitchButton, InfoBar, InfoBarPosition, FluentIcon
)

from ..styles import COLORS
from ..widgets import CustomSpinBox
from ..utils import DEFAULT_OUTPUT_DIR

# ============================================================
# 配置常量定义
# ============================================================

# 默认配置参数
# 这些值会在用户首次使用或恢复默认时生效
DEFAULT_CONFIG = {
    'max_pages': 10,           # 每个公众号最多爬取的页数
    'request_interval': 10,    # 请求间隔（秒）
    'account_interval_min': 15,  # 公众号切换最小间隔（秒）
    'account_interval_max': 30,  # 公众号切换最大间隔（秒）
    'max_workers': 3,          # 默认并发数
    'include_content': False,  # 是否默认获取正文
    'output_dir': DEFAULT_OUTPUT_DIR,  # 输出目录
    'cache_expire_hours': 96,  # 登录缓存有效期（小时）
}

# 配置文件路径
CONFIG_FILE = 'config.json'


class SettingItem(QWidget):
    """
    设置项组件
    
    单个设置项的通用布局组件，左侧显示标题和描述，右侧放置控件。
    
    布局结构：
        ┌─────────────────────────────────────────┐
        │  标题                        [控件区域] │
        │  描述（可选）                           │
        └─────────────────────────────────────────┘
    
    Attributes:
        title_label: 标题标签
        desc_label: 描述标签（可选）
        control_layout: 右侧控件布局
    """
    
    def __init__(self, title, description=None, parent=None):
        """
        初始化设置项
        
        Args:
            title: 设置项标题
            description: 设置项描述（可选）
            parent: 父控件
        """
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(0)
        
        # 左侧文字区域（标题和描述）
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        text_layout.setContentsMargins(0, 0, 0, 0)
        
        self.title_label = BodyLabel(title)
        text_layout.addWidget(self.title_label)
        
        if description:
            self.desc_label = CaptionLabel(description)
            self.desc_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
            text_layout.addWidget(self.desc_label)
        
        layout.addLayout(text_layout)
        layout.addStretch()
        
        # 右侧控件区域
        self.control_layout = QHBoxLayout()
        self.control_layout.setSpacing(8)
        layout.addLayout(self.control_layout)
    
    def addControl(self, widget):
        """
        添加控件到右侧区域
        
        Args:
            widget: 要添加的控件
        """
        self.control_layout.addWidget(widget)


class SettingsPage(ScrollArea):
    """
    设置页面
    
    提供应用程序的全局配置界面，包括爬取参数、存储设置等。
    配置变更会保存到文件并通过信号通知其他组件。
    
    Signals:
        settings_changed: 设置变更信号，参数为新的配置字典
    
    Attributes:
        config: 当前配置字典
    """
    
    # 设置变更信号，当用户保存设置时发射
    settings_changed = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        """
        初始化设置页面
        
        Args:
            parent: 父控件
        """
        super().__init__(parent)
        
        # 加载配置：先使用默认值，再从文件覆盖
        self.config = DEFAULT_CONFIG.copy()
        self._load_config()
        
        # 设置对象名称，用于样式表选择器
        self.setObjectName("settingsPage")
        
        # 构建界面
        self._setup_ui()
        
        # 应用暗黑背景样式
        self._apply_dark_background()
    
    def _apply_dark_background(self):
        """应用暗黑背景样式"""
        self.setStyleSheet("""
            QScrollArea#settingsPage {
                background-color: #1a1a1a;
                border: none;
            }
            QScrollArea#settingsPage > QWidget > QWidget {
                background-color: #1a1a1a;
            }
        """)
    
    def _setup_ui(self):
        self.setWidgetResizable(True)
        container = QWidget()
        self.setWidget(container)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(36, 20, 36, 20)
        layout.setSpacing(12)
        
        layout.addWidget(TitleLabel("系统设置"))
        
        # 爬取设置卡片
        scrape_card = CardWidget()
        scrape_layout = QVBoxLayout(scrape_card)
        scrape_layout.setContentsMargins(20, 16, 20, 16)
        scrape_layout.setSpacing(0)
        
        scrape_title = BodyLabel("爬取设置")
        scrape_title.setStyleSheet("font-weight: bold; font-size: 14px; color: #ffffff;")
        scrape_layout.addWidget(scrape_title)
        
        # 最大页数
        item1 = SettingItem("默认最大页数", "每个公众号最多爬取的页数")
        self.pages_spin = CustomSpinBox(1, 100, self.config.get('max_pages', 10))
        self.pages_spin.setMinimumWidth(120)
        item1.addControl(self.pages_spin)
        scrape_layout.addWidget(item1)
        
        self._add_separator(scrape_layout)
        
        # 请求间隔
        item2 = SettingItem("请求间隔", "每次请求之间的等待时间")
        self.interval_spin = CustomSpinBox(1, 60, self.config.get('request_interval', 10))
        self.interval_spin.setMinimumWidth(120)
        item2.addControl(self.interval_spin)
        item2.addControl(BodyLabel("秒"))
        scrape_layout.addWidget(item2)
        
        self._add_separator(scrape_layout)
        
        # 线程数
        item3 = SettingItem("默认线程数", "批量爬取时的并发数")
        self.workers_spin = CustomSpinBox(1, 10, self.config.get('max_workers', 3))
        self.workers_spin.setMinimumWidth(120)
        item3.addControl(self.workers_spin)
        scrape_layout.addWidget(item3)
        
        self._add_separator(scrape_layout)
        
        # 获取正文
        item4 = SettingItem("获取文章正文", "默认爬取文章内容（较慢）")
        self.content_switch = SwitchButton()
        self.content_switch.setChecked(self.config.get('include_content', False))
        item4.addControl(self.content_switch)
        scrape_layout.addWidget(item4)
        
        layout.addWidget(scrape_card)
        
        # 存储设置卡片
        storage_card = CardWidget()
        storage_layout = QVBoxLayout(storage_card)
        storage_layout.setContentsMargins(20, 16, 20, 16)
        storage_layout.setSpacing(0)
        
        storage_title = BodyLabel("存储设置")
        storage_title.setStyleSheet("font-weight: bold; font-size: 14px; color: #ffffff;")
        storage_layout.addWidget(storage_title)
        
        # 输出目录
        item5 = SettingItem("默认输出目录", "爬取结果保存位置")
        self.output_input = LineEdit()
        # 获取配置中的输出目录，如果是旧值 'results' 则使用新的默认路径
        config_output_dir = self.config.get('output_dir', DEFAULT_OUTPUT_DIR)
        if config_output_dir == 'results':
            config_output_dir = DEFAULT_OUTPUT_DIR
        self.output_input.setText(config_output_dir)
        self.output_input.setMinimumWidth(150)
        self.output_input.setMaximumWidth(250)  # 限制最大宽度，给按钮留出空间
        item5.addControl(self.output_input)
        storage_layout.addWidget(item5)
        
        self._add_separator(storage_layout)
        
        # 缓存有效期
        item6 = SettingItem("登录缓存有效期", "登录信息的保存时长")
        self.cache_spin = CustomSpinBox(1, 168, self.config.get('cache_expire_hours', 96))
        self.cache_spin.setMinimumWidth(120)
        item6.addControl(self.cache_spin)
        item6.addControl(BodyLabel("小时"))
        storage_layout.addWidget(item6)
        
        layout.addWidget(storage_card)
        
        # 关于卡片
        about_card = CardWidget()
        about_layout = QHBoxLayout(about_card)
        about_layout.setContentsMargins(20, 16, 20, 16)
        about_layout.setSpacing(20)
        
        # 左侧应用信息
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        app_name = BodyLabel("微信公众号爬虫")
        app_name.setStyleSheet("font-weight: bold; font-size: 14px; color: #ffffff;")
        info_layout.addWidget(app_name)
        version_label = CaptionLabel("版本 1.0  |  GUI 版本")
        version_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        info_layout.addWidget(version_label)
        about_layout.addLayout(info_layout)
        
        about_layout.addStretch()
        
        # 右侧功能列表
        features = CaptionLabel("扫码登录 · 单个/批量爬取 · 日期筛选 · CSV导出")
        features.setStyleSheet(f"color: {COLORS['text_secondary']};")
        about_layout.addWidget(features)
        
        layout.addWidget(about_card)
        
        # 按钮区域
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        
        save_btn = PrimaryPushButton("保存设置", icon=FluentIcon.SAVE)
        save_btn.setFixedWidth(120)
        save_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(save_btn)
        
        reset_btn = PushButton("恢复默认", icon=FluentIcon.SYNC)
        reset_btn.setFixedWidth(120)
        reset_btn.clicked.connect(self._on_reset)
        btn_layout.addWidget(reset_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        layout.addStretch()
    
    def _add_separator(self, layout):
        """
        添加分隔线
        
        在设置项之间添加水平分隔线，增强视觉层次。
        
        Args:
            layout: 要添加分隔线的布局
        """
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(f"background-color: {COLORS['border']}; max-height: 1px;")
        layout.addWidget(line)
    
    def _load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    self.config.update(json.load(f))
            except Exception:
                pass
    
    def _save_config(self):
        """
        保存配置到文件
        
        将当前配置写入 config.json 文件。
        
        Returns:
            bool: 保存成功返回 True，失败返回 False
        """
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False
    
    def _on_save(self):
        """
        保存设置按钮点击处理
        
        从界面控件收集配置值，保存到文件，并发射设置变更信号。
        """
        # 从界面控件收集配置值
        self.config = {
            'max_pages': self.pages_spin.value(),
            'request_interval': self.interval_spin.value(),
            'max_workers': self.workers_spin.value(),
            'include_content': self.content_switch.isChecked(),
            'output_dir': self.output_input.text().strip() or DEFAULT_OUTPUT_DIR,
            'cache_expire_hours': self.cache_spin.value(),
        }
        if self._save_config():
            self.settings_changed.emit(self.config)
            InfoBar.success(
                title="保存成功", content="设置已保存",
                parent=self, position=InfoBarPosition.TOP, duration=2000
            )
        else:
            InfoBar.error(
                title="保存失败", content="保存设置失败",
                parent=self, position=InfoBarPosition.TOP, duration=3000
            )
    
    def _on_reset(self):
        self.config = DEFAULT_CONFIG.copy()
        self.pages_spin.setValue(self.config['max_pages'])
        self.interval_spin.setValue(self.config['request_interval'])
        self.workers_spin.setValue(self.config['max_workers'])
        self.content_switch.setChecked(self.config['include_content'])
        self.output_input.setText(self.config['output_dir'])
        self.cache_spin.setValue(self.config['cache_expire_hours'])
        self._save_config()
        InfoBar.info(
            title="已恢复", content="设置已恢复为默认值",
            parent=self, position=InfoBarPosition.TOP, duration=2000
        )
    
    def get_config(self):
        """
        获取当前配置
        
        Returns:
            dict: 当前配置的副本
        """
        return self.config.copy()
