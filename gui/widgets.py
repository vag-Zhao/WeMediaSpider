#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
自定义控件模块 - Fluent Design 风格

本模块提供了一系列自定义的 GUI 控件，基于 qfluentwidgets 扩展，
实现了微信风格的暗黑主题设计。

控件列表:
    基础控件:
        - CustomSpinBox: 带 Fluent 样式的数字输入框
        - CardWidget: 卡片容器控件
        - ProgressWidget: 进度显示控件（支持确定/不确定模式）
    
    输入控件:
        - AccountListWidget: 公众号列表输入控件（支持历史记录）
    
    对话框:
        - ArticlePreviewDialog: 全屏文章预览对话框
    
    历史记录组件:
        - HistoryTagWidget: 单个历史记录标签
        - HistoryTagsContainer: 历史记录标签容器

工具函数:
    - create_fluent_spinbox(): 创建带样式的 SpinBox

样式常量:
    - SPINBOX_DARK_QSS: SpinBox 深色主题样式
    - SPINBOX_LIGHT_QSS: SpinBox 浅色主题样式

设计特点:
    1. 所有控件都适配暗黑主题
    2. 使用微信绿作为强调色
    3. 圆角设计，现代化外观
    4. 流畅的悬停和点击动画
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSizePolicy,
    QDialog, QLabel, QScrollArea, QApplication, QFrame
)
from PyQt6.QtCore import pyqtSignal, Qt, QUrl, QSize
from PyQt6.QtGui import QDesktopServices, QKeyEvent, QCursor

from qfluentwidgets import (
    CardWidget as FluentCard, PrimaryPushButton, PushButton,
    ProgressBar, BodyLabel, StrongBodyLabel, CaptionLabel,
    IconWidget, FluentIcon, PlainTextEdit, SpinBox, setCustomStyleSheet,
    TitleLabel, TextEdit, ToolTipFilter, ToolTipPosition, FlowLayout
)

from .styles import COLORS


# SpinBox 深色主题样式 - Fluent Design 风格
# 注意：右侧需要预留 36px 给箭头按钮
SPINBOX_DARK_QSS = """
SpinBox {
    background-color: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 5px;
    padding: 5px 36px 5px 10px;
    color: rgba(255, 255, 255, 0.9);
    font-size: 14px;
    selection-background-color: #0078d4;
    min-height: 18px;
}
SpinBox:hover {
    background-color: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.12);
}
SpinBox:focus {
    border: 1px solid #0078d4;
    background-color: rgba(255, 255, 255, 0.05);
}
SpinBox:disabled {
    color: rgba(255, 255, 255, 0.36);
    background-color: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.05);
}
"""

SPINBOX_LIGHT_QSS = """
SpinBox {
    background-color: rgba(255, 255, 255, 0.7);
    border: 1px solid rgba(0, 0, 0, 0.08);
    border-radius: 5px;
    padding: 5px 36px 5px 10px;
    color: rgba(0, 0, 0, 0.9);
    font-size: 14px;
    selection-background-color: #0078d4;
    min-height: 18px;
}
SpinBox:hover {
    background-color: rgba(249, 249, 249, 0.9);
    border: 1px solid rgba(0, 0, 0, 0.12);
}
SpinBox:focus {
    border: 1px solid #0078d4;
    background-color: white;
}
SpinBox:disabled {
    color: rgba(0, 0, 0, 0.36);
    background-color: rgba(249, 249, 249, 0.3);
    border: 1px solid rgba(0, 0, 0, 0.05);
}
"""


def create_fluent_spinbox(min_val=1, max_val=100, default_val=10, width=None):
    """创建带 Fluent Design 样式的 SpinBox
    
    这是创建数字输入框的推荐方式，会自动应用深色主题样式。
    
    Args:
        min_val: 最小值，默认为 1
        max_val: 最大值，默认为 100
        default_val: 默认值，默认为 10
        width: 固定宽度（像素），None 表示自动宽度
    
    Returns:
        配置好样式的 SpinBox 实例
    
    示例:
        >>> spinbox = create_fluent_spinbox(1, 50, 10, width=120)
        >>> layout.addWidget(spinbox)
    """
    spinbox = SpinBox()
    spinbox.setRange(min_val, max_val)
    spinbox.setValue(default_val)
    
    if width:
        spinbox.setFixedWidth(width)
    
    # 应用自定义深色主题样式
    setCustomStyleSheet(spinbox, SPINBOX_LIGHT_QSS, SPINBOX_DARK_QSS)
    
    return spinbox


class CustomSpinBox(SpinBox):
    """自定义 SpinBox 控件
    
    继承自 qfluentwidgets 的 SpinBox，自动应用 Fluent Design 深色主题样式。
    保留此类是为了向后兼容，新代码推荐使用 create_fluent_spinbox() 函数。
    
    Args:
        min_val: 最小值
        max_val: 最大值
        default_val: 默认值
        parent: 父控件
    """
    
    def __init__(self, min_val=1, max_val=100, default_val=10, parent=None):
        """初始化 SpinBox 并应用样式"""
        super().__init__(parent)
        self.setRange(min_val, max_val)
        self.setValue(default_val)
        # 应用自定义深色主题样式
        setCustomStyleSheet(self, SPINBOX_LIGHT_QSS, SPINBOX_DARK_QSS)
    
    def setMinimumWidth(self, width):
        """设置最小宽度"""
        super().setMinimumWidth(width)


class CardWidget(FluentCard):
    """卡片容器控件
    
    基于 qfluentwidgets 的 CardWidget，提供带标题的卡片布局。
    内部使用垂直布局，可以通过 addWidget/addLayout 添加内容。
    
    Args:
        title: 卡片标题，None 表示无标题
        parent: 父控件
    
    示例:
        >>> card = CardWidget("设置", parent)
        >>> card.addWidget(QLabel("选项1"))
        >>> card.addWidget(QCheckBox("启用"))
    """
    
    def __init__(self, title=None, parent=None):
        """初始化卡片，设置内边距和间距"""
        super().__init__(parent)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(12)
        
        if title:
            title_label = StrongBodyLabel(title)
            self.main_layout.addWidget(title_label)
    
    def addWidget(self, widget):
        self.main_layout.addWidget(widget)
    
    def addLayout(self, layout):
        self.main_layout.addLayout(layout)


class ProgressWidget(QWidget):
    """进度显示控件
    
    支持两种进度模式：
    1. 确定模式: 显示具体的百分比进度
    2. 不确定模式: 显示脉冲动画，用于无法预估进度的任务
    
    显示内容包括：
    - 状态文字（左侧）
    - 文章数量（右侧，绿色）
    - 百分比（右侧，仅确定模式）
    - 进度条（底部）
    
    Signals:
        cancel_clicked: 取消按钮点击信号（预留）
    
    Attributes:
        _indeterminate: 是否为不确定模式
        _article_count: 已获取的文章数量
        _current_account: 当前正在爬取的账号
    """
    
    cancel_clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        """初始化进度控件"""
        super().__init__(parent)
        self._indeterminate = False
        self._pulse_value = 0
        self._pulse_direction = 1
        self._article_count = 0
        self._current_account = ""
        self._total_accounts = 0
        self._current_account_index = 0
        self._setup_ui()
        self._setup_timer()
    
    def _setup_ui(self):
        """设置 UI 布局，包含信息行和进度条"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        
        # 第一行：状态信息 + 文章数量 + 百分比
        info_layout = QHBoxLayout()
        info_layout.setSpacing(8)
        
        # 左侧：状态文字
        self.progress_label = BodyLabel("准备中...")
        self.progress_label.setMinimumWidth(200)
        info_layout.addWidget(self.progress_label)
        
        info_layout.addStretch()
        
        # 右侧：文章数量 + 百分比
        # 文章数量标签
        self.article_label = BodyLabel("")
        self.article_label.setStyleSheet(f"color: {COLORS['success']}; font-weight: 500;")
        info_layout.addWidget(self.article_label)
        
        # 百分比标签
        self.percent_label = StrongBodyLabel("")
        self.percent_label.setStyleSheet(f"color: {COLORS['primary']}; min-width: 50px;")
        info_layout.addWidget(self.percent_label)
        
        layout.addLayout(info_layout)
        
        # 进度条
        self.progress_bar = ProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(4)
        layout.addWidget(self.progress_bar)
    
    def _setup_timer(self):
        """设置不确定模式的动画定时器"""
        from PyQt6.QtCore import QTimer
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._pulse_animation)
        self._timer.setInterval(50)  # 50ms for smooth animation
    
    def _pulse_animation(self):
        """执行脉冲动画，在 20-80 之间来回变化"""
        if not self._indeterminate:
            return
        
        # Create a smooth pulse animation between 20-80
        self._pulse_value += self._pulse_direction * 2
        if self._pulse_value >= 80:
            self._pulse_direction = -1
        elif self._pulse_value <= 20:
            self._pulse_direction = 1
        
        self.progress_bar.setValue(self._pulse_value)
    
    def set_indeterminate(self, message="处理中...", count_text=""):
        """设置为不确定进度模式
        
        启动脉冲动画，适用于无法预估进度的任务。
        
        Args:
            message: 状态文字
            count_text: 计数文字（可选）
        """
        self._indeterminate = True
        self._pulse_value = 20
        self._pulse_direction = 1
        self.progress_label.setText(message)
        if count_text:
            self.article_label.setText(count_text)
        self._timer.start()
    
    def set_progress(self, current, total, message=None):
        """设置确定进度模式
        
        显示具体的百分比进度，会自动停止脉冲动画。
        
        Args:
            current: 当前进度值
            total: 总进度值
            message: 状态文字（可选）
        """
        # Stop animation if running
        if self._indeterminate:
            self._indeterminate = False
            self._timer.stop()
        
        if total > 0:
            percent = int(current / total * 100)
            self.progress_bar.setValue(percent)
            self.percent_label.setText(f"{percent}%")
        if message:
            self.progress_label.setText(message)
        else:
            self.progress_label.setText(f"进度: {current}/{total}")
    
    def set_article_progress(self, count, message):
        """设置文章进度（不确定模式）
        
        显示已获取的文章数量，同时启动脉冲动画。
        
        Args:
            count: 已获取的文章数量
            message: 状态文字
        """
        self._article_count = count
        
        if not self._indeterminate:
            self._indeterminate = True
            self._pulse_value = 20
            self._pulse_direction = 1
            self._timer.start()
        
        self.progress_label.setText(message)
        self.article_label.setText(f"📄 已获取 {count} 篇文章")
        # 不确定模式下不显示百分比
        self.percent_label.setText("")
    
    def set_scrape_progress(self, account_index, total_accounts, article_count, current_account=""):
        """设置爬取进度（确定模式）
        
        显示账号进度百分比和文章数量，适用于批量爬取任务。
        
        Args:
            account_index: 当前账号索引（从 1 开始）
            total_accounts: 总账号数
            article_count: 已获取的文章数量
            current_account: 当前正在爬取的账号名称
        """
        self._article_count = article_count
        self._current_account = current_account
        self._total_accounts = total_accounts
        self._current_account_index = account_index
        
        # 停止动画，使用确定进度
        if self._indeterminate:
            self._indeterminate = False
            self._timer.stop()
        
        # 计算百分比
        if total_accounts > 0:
            percent = int(account_index / total_accounts * 100)
            self.progress_bar.setValue(percent)
            self.percent_label.setText(f"{percent}%")
        
        # 更新状态文字
        if current_account:
            self.progress_label.setText(f"正在爬取: {current_account} ({account_index}/{total_accounts})")
        else:
            self.progress_label.setText(f"爬取进度: {account_index}/{total_accounts}")
        
        # 更新文章数量
        self.article_label.setText(f"📄 已获取 {article_count} 篇文章")
    
    def update_article_count(self, count):
        """仅更新文章数量显示，不改变进度模式"""
        self._article_count = count
        self.article_label.setText(f"📄 已获取 {count} 篇文章")
    
    def reset(self):
        """重置进度控件到初始状态"""
        self._indeterminate = False
        self._timer.stop()
        self._article_count = 0
        self._current_account = ""
        self._total_accounts = 0
        self._current_account_index = 0
        self.progress_bar.setValue(0)
        self.percent_label.setText("")
        self.article_label.setText("")
        self.progress_label.setText("准备中...")
    
    def set_complete(self, message="完成"):
        """设置为完成状态，显示 100% 进度"""
        self._indeterminate = False
        self._timer.stop()
        self.progress_bar.setValue(100)
        self.percent_label.setText("100%")
        self.article_label.setText(f"📄 共获取 {self._article_count} 篇文章")
        self.progress_label.setText(message)


class AccountListWidget(QWidget):
    """公众号列表输入控件
    
    提供多行文本输入框，支持输入多个公众号名称。
    支持多种分隔符：换行、逗号、分号、顿号、空格、制表符、竖线。
    
    特性:
        - 实时显示已输入的公众号数量
        - 集成历史记录功能，显示最近搜索的公众号
        - 点击历史标签可快速添加到输入框
        - 支持清空列表操作
    
    Attributes:
        _history_manager: 历史记录管理器实例
        text_edit: 多行文本输入框
        count_label: 公众号计数标签
        history_container: 历史记录标签容器
    """
    
    def __init__(self, parent=None):
        """初始化控件并加载历史记录"""
        super().__init__(parent)
        self._history_manager = None
        self._setup_ui()
        self._load_history()
    
    def _setup_ui(self):
        """设置 UI 布局，包含输入框、计数标签和历史记录"""
        import re
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        hint_label = CaptionLabel("输入公众号名称，每行一个，或用逗号分隔")
        layout.addWidget(hint_label)
        
        self.text_edit = PlainTextEdit()
        self.text_edit.setPlaceholderText("例如:\n人民日报\n新华社\n央视新闻")
        self.text_edit.setMinimumHeight(150)
        layout.addWidget(self.text_edit)
        
        # 底部行：计数 + 清空按钮
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(8)
        
        self.count_label = CaptionLabel("已输入 0 个公众号")
        bottom_layout.addWidget(self.count_label)
        
        bottom_layout.addStretch()
        
        # 清空列表按钮
        self.clear_list_btn = PushButton("清空列表", icon=FluentIcon.DELETE)
        self.clear_list_btn.setFixedHeight(28)
        self.clear_list_btn.clicked.connect(self.clear)
        bottom_layout.addWidget(self.clear_list_btn)
        
        layout.addLayout(bottom_layout)
        
        # 历史记录标签容器
        self.history_container = HistoryTagsContainer()
        self.history_container.tag_clicked.connect(self._on_history_tag_clicked)
        self.history_container.tag_deleted.connect(self._on_history_tag_deleted)
        self.history_container.clear_all.connect(self._on_clear_all_history)
        layout.addWidget(self.history_container)
        
        self.text_edit.textChanged.connect(self._update_count)
    
    def _load_history(self):
        """从历史记录管理器加载数据并显示"""
        try:
            from .history_manager import get_history_manager
            self._history_manager = get_history_manager()
            history = self._history_manager.get_accounts()
            self.history_container.set_history(history)
        except Exception as e:
            print(f"加载历史记录失败: {e}")
    
    def _on_history_tag_clicked(self, account_name: str):
        """处理历史标签点击事件，将公众号添加到输入框"""
        current_text = self.text_edit.toPlainText().strip()
        current_accounts = self.get_accounts()
        
        # 检查是否已存在
        if account_name in current_accounts:
            return
        
        # 添加到输入框
        if current_text:
            new_text = current_text + '\n' + account_name
        else:
            new_text = account_name
        
        self.text_edit.setPlainText(new_text)
    
    def _on_history_tag_deleted(self, account_name: str):
        """处理历史标签删除事件"""
        if self._history_manager:
            self._history_manager.remove_account(account_name)
            self.history_container.remove_tag(account_name)
    
    def _on_clear_all_history(self):
        """处理清空所有历史事件"""
        if self._history_manager:
            self._history_manager.clear()
    
    def add_to_history(self, accounts: list):
        """将公众号列表添加到历史记录
        
        爬取完成后调用此方法保存搜索历史。
        
        Args:
            accounts: 公众号名称列表
        """
        if self._history_manager and accounts:
            for account in accounts:
                self._history_manager.add_account(account)
            # 刷新显示
            history = self._history_manager.get_accounts()
            self.history_container.set_history(history)
    
    def refresh_history(self):
        """刷新历史记录显示，从管理器重新加载数据"""
        if self._history_manager:
            history = self._history_manager.get_accounts()
            self.history_container.set_history(history)
    
    def _update_count(self):
        """更新公众号计数显示"""
        accounts = self.get_accounts()
        self.count_label.setText(f"已输入 {len(accounts)} 个公众号")
    
    def get_accounts(self) -> list:
        """获取输入的公众号列表
        
        解析输入框内容，支持多种分隔符。
        
        Returns:
            去重后的公众号名称列表
        """
        import re
        text = self.text_edit.toPlainText().strip()
        if not text:
            return []
        accounts = re.split(r'[\n\r,;，；、\s\t|]+', text)
        return [acc.strip() for acc in accounts if acc.strip()]
    
    def set_accounts(self, accounts: list):
        """设置输入框内容
        
        Args:
            accounts: 公众号名称列表，会以换行符连接
        """
        self.text_edit.setPlainText('\n'.join(accounts))
    
    def clear(self):
        """清空输入框内容"""
        self.text_edit.clear()


class ArticlePreviewDialog(QDialog):
    """全屏文章预览对话框
    
    提供全屏预览文章内容的功能，支持：
    - 上一篇/下一篇切换（按钮或键盘快捷键）
    - 在浏览器中打开原文链接
    - 显示文章标题、公众号、发布时间
    - 滚动查看文章内容
    
    快捷键:
        - 左方向键/A: 上一篇
        - 右方向键/D: 下一篇
        - ESC: 关闭对话框
    
    Signals:
        article_changed: 文章切换信号，携带新的文章索引
    
    Attributes:
        articles: 文章列表
        current_index: 当前显示的文章索引
    """
    
    article_changed = pyqtSignal(int)
    
    def __init__(self, parent=None):
        """初始化对话框，设置为屏幕 90% 大小"""
        super().__init__(parent)
        self.articles = []  # 文章列表
        self.current_index = 0  # 当前文章索引
        self._setup_ui()
        self._setup_shortcuts()
    
    def _setup_ui(self):
        """设置 UI 布局，包含工具栏、文章信息和内容区域"""
        self.setWindowTitle("文章预览")
        self.setModal(True)
        
        # 设置窗口大小为屏幕的90%
        screen = QApplication.primaryScreen()
        if screen:
            screen_size = screen.availableGeometry()
            width = int(screen_size.width() * 0.9)
            height = int(screen_size.height() * 0.9)
            self.resize(width, height)
            # 居中显示
            x = (screen_size.width() - width) // 2
            y = (screen_size.height() - height) // 2
            self.move(x, y)
        
        # 设置样式
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {COLORS['background']};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 顶部工具栏
        toolbar = QWidget()
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        toolbar_layout.setSpacing(10)
        
        # 上一篇按钮
        self.prev_btn = PushButton("上一篇", icon=FluentIcon.LEFT_ARROW)
        self.prev_btn.setFixedWidth(120)
        self.prev_btn.clicked.connect(self._on_prev)
        toolbar_layout.addWidget(self.prev_btn)
        
        # 文章计数标签
        self.count_label = BodyLabel("0 / 0")
        self.count_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 14px;")
        toolbar_layout.addWidget(self.count_label)
        
        # 下一篇按钮
        self.next_btn = PushButton("下一篇", icon=FluentIcon.RIGHT_ARROW)
        self.next_btn.setFixedWidth(120)
        self.next_btn.clicked.connect(self._on_next)
        toolbar_layout.addWidget(self.next_btn)
        
        toolbar_layout.addStretch()
        
        # 在浏览器中打开按钮
        self.open_link_btn = PushButton("在浏览器中打开", icon=FluentIcon.LINK)
        self.open_link_btn.setFixedWidth(150)
        self.open_link_btn.clicked.connect(self._on_open_link)
        toolbar_layout.addWidget(self.open_link_btn)
        
        # 关闭按钮
        close_btn = PrimaryPushButton("关闭", icon=FluentIcon.CLOSE)
        close_btn.setFixedWidth(100)
        close_btn.clicked.connect(self.close)
        toolbar_layout.addWidget(close_btn)
        
        layout.addWidget(toolbar)
        
        # 文章信息卡片
        info_card = FluentCard()
        info_layout = QVBoxLayout(info_card)
        info_layout.setContentsMargins(20, 15, 20, 15)
        info_layout.setSpacing(8)
        
        # 标题
        self.title_label = TitleLabel("文章标题")
        self.title_label.setWordWrap(True)
        self.title_label.setStyleSheet(f"color: {COLORS['text']}; font-size: 24px; font-weight: bold;")
        info_layout.addWidget(self.title_label)
        
        # 元信息行
        meta_layout = QHBoxLayout()
        meta_layout.setSpacing(20)
        
        self.account_label = BodyLabel("公众号: -")
        self.account_label.setStyleSheet(f"color: {COLORS['primary']}; font-size: 14px;")
        meta_layout.addWidget(self.account_label)
        
        self.time_label = BodyLabel("发布时间: -")
        self.time_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 14px;")
        meta_layout.addWidget(self.time_label)
        
        meta_layout.addStretch()
        info_layout.addLayout(meta_layout)
        
        layout.addWidget(info_card)
        
        # 内容区域
        content_card = FluentCard()
        content_layout = QVBoxLayout(content_card)
        content_layout.setContentsMargins(0, 0, 0, 0)
        
        # 使用滚动区域包装内容
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: transparent;
            }}
            QScrollBar:vertical {{
                background-color: {COLORS['surface']};
                width: 10px;
                border-radius: 5px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {COLORS['border']};
                border-radius: 5px;
                min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {COLORS['primary']};
            }}
        """)
        
        # 内容文本框
        self.content_text = TextEdit()
        self.content_text.setReadOnly(True)
        self.content_text.setStyleSheet(f"""
            TextEdit {{
                background-color: {COLORS['surface']};
                color: {COLORS['text']};
                border: none;
                padding: 20px;
                font-size: 15px;
                line-height: 1.8;
            }}
        """)
        self.content_text.setPlaceholderText("无内容")
        
        scroll_area.setWidget(self.content_text)
        content_layout.addWidget(scroll_area)
        
        layout.addWidget(content_card, 1)  # 内容区域占据剩余空间
        
        # 底部提示
        hint_label = BodyLabel("提示: 使用 ← → 方向键或 A/D 键切换文章，按 ESC 关闭")
        hint_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")
        hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hint_label)
    
    def _setup_shortcuts(self):
        """设置快捷键（在 keyPressEvent 中实现）"""
        pass
    
    def keyPressEvent(self, event: QKeyEvent):
        """处理键盘事件，实现快捷键功能"""
        key = event.key()
        
        # 左方向键或A键 - 上一篇
        if key == Qt.Key.Key_Left or key == Qt.Key.Key_A:
            self._on_prev()
            return
        
        # 右方向键或D键 - 下一篇
        if key == Qt.Key.Key_Right or key == Qt.Key.Key_D:
            self._on_next()
            return
        
        # ESC键 - 关闭
        if key == Qt.Key.Key_Escape:
            self.close()
            return
        
        # 其他键交给父类处理
        super().keyPressEvent(event)
    
    def set_articles(self, articles: list, current_index: int = 0):
        """设置文章列表并显示指定文章
        
        Args:
            articles: 文章列表，每篇文章是字典，包含以下字段：
                - 公众号: 公众号名称
                - 标题: 文章标题
                - 发布时间: 发布时间字符串
                - 链接: 文章原文链接
                - 内容: 文章正文内容
            current_index: 初始显示的文章索引，默认为 0
        """
        self.articles = articles
        self.current_index = max(0, min(current_index, len(articles) - 1)) if articles else 0
        self._update_display()
    
    def _update_display(self):
        """更新界面显示，包括标题、元信息、内容和按钮状态"""
        if not self.articles:
            self.title_label.setText("无文章")
            self.account_label.setText("公众号: -")
            self.time_label.setText("发布时间: -")
            self.content_text.setText("")
            self.count_label.setText("0 / 0")
            self.prev_btn.setEnabled(False)
            self.next_btn.setEnabled(False)
            self.open_link_btn.setEnabled(False)
            return
        
        # 获取当前文章
        article = self.articles[self.current_index]
        
        # 更新标题
        title = article.get('标题', '无标题')
        self.title_label.setText(title)
        self.setWindowTitle(f"文章预览 - {title}")
        
        # 更新元信息
        account = article.get('公众号', '-')
        self.account_label.setText(f"📱 公众号: {account}")
        
        pub_time = article.get('发布时间', '-')
        self.time_label.setText(f"📅 发布时间: {pub_time}")
        
        # 更新内容
        content = article.get('内容', '')
        self.content_text.setText(content if content else "无内容")
        
        # 滚动到顶部
        self.content_text.verticalScrollBar().setValue(0)
        
        # 更新计数
        self.count_label.setText(f"{self.current_index + 1} / {len(self.articles)}")
        
        # 更新按钮状态
        self.prev_btn.setEnabled(self.current_index > 0)
        self.next_btn.setEnabled(self.current_index < len(self.articles) - 1)
        
        # 检查是否有链接
        link = article.get('链接', '')
        self.open_link_btn.setEnabled(bool(link))
    
    def _on_prev(self):
        """切换到上一篇文章"""
        if self.current_index > 0:
            self.current_index -= 1
            self._update_display()
            self.article_changed.emit(self.current_index)
    
    def _on_next(self):
        """切换到下一篇文章"""
        if self.current_index < len(self.articles) - 1:
            self.current_index += 1
            self._update_display()
            self.article_changed.emit(self.current_index)
    
    def _on_open_link(self):
        """在默认浏览器中打开文章原文链接"""
        if self.articles and 0 <= self.current_index < len(self.articles):
            link = self.articles[self.current_index].get('链接', '')
            if link:
                QDesktopServices.openUrl(QUrl(link))
    
    def go_to_article(self, index: int):
        """跳转到指定索引的文章
        
        外部调用此方法可以同步对话框显示的文章。
        
        Args:
            index: 目标文章索引（从 0 开始）
        """
        if 0 <= index < len(self.articles):
            self.current_index = index
            self._update_display()


# ============== 历史记录标签组件 ==============

class HistoryTagWidget(QWidget):
    """单个历史记录标签控件
    
    微信风格的标签设计，用于显示单个公众号的历史记录。
    
    交互特性:
        - 点击标签: 将公众号名称添加到输入框
        - 悬停效果: 显示绿色边框和删除按钮
        - 删除按钮: 从历史记录中移除该公众号
    
    视觉设计:
        - 默认状态: 半透明灰色背景，白色文字
        - 悬停状态: 绿色边框，绿色文字，显示删除按钮
    
    Signals:
        clicked: 点击标签时发出，携带公众号名称
        deleted: 删除标签时发出，携带公众号名称
    
    Attributes:
        account_name: 公众号名称
        _hovered: 是否处于悬停状态
    """
    
    clicked = pyqtSignal(str)
    deleted = pyqtSignal(str)
    
    def __init__(self, account_name: str, parent=None):
        """初始化标签控件
        
        Args:
            account_name: 公众号名称
            parent: 父控件
        """
        super().__init__(parent)
        self.account_name = account_name
        self._hovered = False
        self._setup_ui()
        self._setup_style()
    
    def _setup_ui(self):
        """设置 UI 布局，包含名称标签和删除按钮"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(6)
        
        # 公众号名称标签
        self.name_label = BodyLabel(self.account_name)
        self.name_label.setStyleSheet("background: transparent; border: none;")
        layout.addWidget(self.name_label)
        
        # 删除按钮（默认隐藏）
        self.delete_btn = PushButton()
        self.delete_btn.setIcon(FluentIcon.CLOSE)
        self.delete_btn.setFixedSize(16, 16)
        self.delete_btn.setIconSize(QSize(10, 10))
        self.delete_btn.clicked.connect(self._on_delete)
        self.delete_btn.setVisible(False)
        self.delete_btn.setStyleSheet("""
            PushButton {
                background-color: transparent;
                border: none;
                border-radius: 8px;
                padding: 0px;
            }
            PushButton:hover {
                background-color: rgba(255, 100, 100, 0.3);
            }
        """)
        layout.addWidget(self.delete_btn)
        
        # 设置鼠标追踪以检测悬停
        self.setMouseTracking(True)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        
        # 添加工具提示
        self.installEventFilter(ToolTipFilter(self, showDelay=500, position=ToolTipPosition.TOP))
        self.setToolTip(f"点击添加「{self.account_name}」到输入框")
    
    def _setup_style(self):
        """初始化样式"""
        self._update_style()
    
    def _update_style(self):
        """根据悬停状态更新样式"""
        if self._hovered:
            # 悬停状态 - 微信绿色高亮
            self.setStyleSheet(f"""
                HistoryTagWidget {{
                    background-color: rgba(7, 193, 96, 0.15);
                    border: 1px solid {COLORS['primary']};
                    border-radius: 15px;
                }}
            """)
            self.name_label.setStyleSheet(f"""
                BodyLabel {{
                    color: {COLORS['primary']};
                    background: transparent;
                    border: none;
                    font-weight: 500;
                }}
            """)
        else:
            # 默认状态
            self.setStyleSheet(f"""
                HistoryTagWidget {{
                    background-color: rgba(255, 255, 255, 0.08);
                    border: 1px solid rgba(255, 255, 255, 0.12);
                    border-radius: 15px;
                }}
            """)
            self.name_label.setStyleSheet(f"""
                BodyLabel {{
                    color: {COLORS['text']};
                    background: transparent;
                    border: none;
                }}
            """)
    
    def enterEvent(self, event):
        """处理鼠标进入事件，显示悬停效果"""
        self._hovered = True
        self._update_style()
        self.delete_btn.setVisible(True)
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """处理鼠标离开事件，恢复默认样式"""
        self._hovered = False
        self._update_style()
        self.delete_btn.setVisible(False)
        super().leaveEvent(event)
    
    def mousePressEvent(self, event):
        """处理鼠标点击事件，发出 clicked 信号"""
        if event.button() == Qt.MouseButton.LeftButton:
            # 检查是否点击在删除按钮上
            if not self.delete_btn.geometry().contains(event.pos()):
                self.clicked.emit(self.account_name)
        super().mousePressEvent(event)
    
    def _on_delete(self):
        """处理删除按钮点击，发出 deleted 信号"""
        self.deleted.emit(self.account_name)


class HistoryTagsContainer(QWidget):
    """历史记录标签容器
    
    使用流式布局（FlowLayout）显示所有历史记录标签，
    标签会自动换行以适应容器宽度。
    
    布局结构:
        - 标题行: 历史图标 + "搜索历史" + 清空按钮
        - 分隔线
        - 标签区域: 流式布局的标签列表
        - 空提示: 无历史时显示
    
    Signals:
        tag_clicked: 标签被点击，携带公众号名称
        tag_deleted: 标签被删除，携带公众号名称
        clear_all: 清空所有历史
    
    Attributes:
        _tags: 标签控件列表
        flow_layout: 流式布局实例
    """
    
    tag_clicked = pyqtSignal(str)
    tag_deleted = pyqtSignal(str)
    clear_all = pyqtSignal()
    
    def __init__(self, parent=None):
        """初始化容器，默认隐藏"""
        super().__init__(parent)
        self._tags = []  # 存储标签控件
        self._setup_ui()
    
    def _setup_ui(self):
        """设置 UI 布局"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 8, 0, 0)
        main_layout.setSpacing(8)
        
        # 标题行
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)
        
        # 历史图标和标题
        history_icon = IconWidget(FluentIcon.HISTORY)
        history_icon.setFixedSize(14, 14)
        header_layout.addWidget(history_icon)
        
        title_label = CaptionLabel("搜索历史")
        title_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # 清空按钮
        self.clear_btn = PushButton("清空")
        self.clear_btn.setFixedHeight(24)
        self.clear_btn.setStyleSheet(f"""
            PushButton {{
                background-color: transparent;
                border: none;
                color: {COLORS['text_secondary']};
                font-size: 12px;
                padding: 2px 8px;
            }}
            PushButton:hover {{
                color: {COLORS['error']};
            }}
        """)
        self.clear_btn.clicked.connect(self._on_clear_all)
        header_layout.addWidget(self.clear_btn)
        
        main_layout.addLayout(header_layout)
        
        # 分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet(f"background-color: rgba(255, 255, 255, 0.08);")
        separator.setFixedHeight(1)
        main_layout.addWidget(separator)
        
        # 标签流式布局容器
        self.tags_widget = QWidget()
        self.flow_layout = FlowLayout(self.tags_widget, needAni=False)
        self.flow_layout.setContentsMargins(0, 4, 0, 4)
        self.flow_layout.setHorizontalSpacing(8)
        self.flow_layout.setVerticalSpacing(8)
        
        main_layout.addWidget(self.tags_widget)
        
        # 无历史提示
        self.empty_label = CaptionLabel("暂无搜索历史")
        self.empty_label.setStyleSheet(f"color: {COLORS['text_secondary']}; padding: 10px 0;")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.empty_label)
        
        # 默认隐藏整个容器
        self.setVisible(False)
    
    def set_history(self, accounts: list):
        """设置历史记录列表
        
        清除现有标签并创建新的标签列表。
        如果列表为空，显示空提示并隐藏容器。
        
        Args:
            accounts: 公众号名称列表
        """
        # 清除现有标签
        self._clear_tags()
        
        if not accounts:
            self.empty_label.setVisible(True)
            self.tags_widget.setVisible(False)
            self.setVisible(False)
            return
        
        self.empty_label.setVisible(False)
        self.tags_widget.setVisible(True)
        self.setVisible(True)
        
        # 创建新标签
        for account in accounts:
            tag = HistoryTagWidget(account)
            tag.clicked.connect(self._on_tag_clicked)
            tag.deleted.connect(self._on_tag_deleted)
            self.flow_layout.addWidget(tag)
            self._tags.append(tag)
    
    def _clear_tags(self):
        """清除所有标签控件并释放资源"""
        for tag in self._tags:
            self.flow_layout.removeWidget(tag)
            tag.deleteLater()
        self._tags.clear()
    
    def _on_tag_clicked(self, account_name: str):
        """转发标签点击信号"""
        self.tag_clicked.emit(account_name)
    
    def _on_tag_deleted(self, account_name: str):
        """转发标签删除信号"""
        self.tag_deleted.emit(account_name)
    
    def _on_clear_all(self):
        """处理清空按钮点击，清除所有标签并发出信号"""
        self.clear_all.emit()
        self._clear_tags()
        self.empty_label.setVisible(True)
        self.tags_widget.setVisible(False)
        self.setVisible(False)
    
    def remove_tag(self, account_name: str):
        """移除指定的标签控件
        
        从布局中移除标签并释放资源。
        如果移除后没有标签了，显示空提示。
        
        Args:
            account_name: 要移除的公众号名称
        """
        for tag in self._tags[:]:
            if tag.account_name == account_name:
                self.flow_layout.removeWidget(tag)
                tag.deleteLater()
                self._tags.remove(tag)
                break
        
        # 如果没有标签了，显示空提示
        if not self._tags:
            self.empty_label.setVisible(True)
            self.tags_widget.setVisible(False)
            self.setVisible(False)
