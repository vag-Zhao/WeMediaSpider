#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
应用程序入口模块

本模块是 GUI 应用的启动入口，负责以下核心功能：
1. 初始化 PyQt6 应用程序实例
2. 配置高 DPI 支持和默认字体
3. 设置 qfluentwidgets 的暗黑主题和微信绿主题色
4. 应用全局暗黑主题样式表
5. 创建并显示主窗口

全局样式表说明:
    DARK_THEME_STYLESHEET 定义了完整的暗黑主题样式，覆盖了：
    - 主窗口和所有 QWidget 的背景色
    - FluentWindow 内部组件的样式
    - 输入框、按钮、表格、滚动条等控件的样式
    - qfluentwidgets 标签组件的透明背景处理

关于标签透明背景问题:
    qfluentwidgets 的标签组件（如 BodyLabel、TitleLabel）在暗黑主题下
    可能显示白色背景。apply_label_transparent_background() 函数通过
    递归遍历所有子组件，强制设置标签的背景为透明来解决这个问题。

使用方式:
    rom gui.app import run_app
    run_app()

    或者直接运行本模块：
    $ python -m gui.app
"""

import sys


# 全局暗黑主题样式表
DARK_THEME_STYLESHEET = """
/* 全局暗黑主题样式 */

/* 主窗口和所有QWidget背景 */
QWidget {
    background-color: #1a1a1a;
    color: #ffffff;
}

/* FluentWindow 内部组件强制暗黑背景 */
FluentWindow, FluentWindow > QWidget {
    background-color: #1a1a1a;
}

/* StackedWidget 和其内部容器 - 关键修复 */
QStackedWidget {
    background-color: #1a1a1a;
    border: none;
}

QStackedWidget > QWidget {
    background-color: #1a1a1a;
}

/* FluentWindow 的 stackedWidget 容器 */
#stackedWidget {
    background-color: #1a1a1a;
}

/* 页面容器背景 */
SimpleCardWidget, CardWidget {
    background-color: #2d2d2d;
}

/* ScrollArea 背景 */
QScrollArea {
    background-color: #1a1a1a;
    border: none;
}

QScrollArea > QWidget > QWidget {
    background-color: #1a1a1a;
}

/* QScrollArea 的 viewport */
QScrollArea > QWidget#qt_scrollarea_viewport {
    background-color: #1a1a1a;
}

/* SingleDirectionScrollArea 和其他滚动区域 */
SingleDirectionScrollArea, SmoothScrollArea {
    background-color: #1a1a1a;
    border: none;
}

SingleDirectionScrollArea > QWidget, SmoothScrollArea > QWidget {
    background-color: #1a1a1a;
}

/* CardWidget 暗黑样式 */
CardWidget {
    background-color: #2d2d2d;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 8px;
}

CardWidget:hover {
    background-color: #363636;
    border: 1px solid rgba(7, 193, 96, 0.3);
}

/* 输入框暗黑样式 */
QLineEdit, LineEdit {
    background-color: #2d2d2d;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 6px;
    padding: 8px 12px;
    color: #ffffff;
}

QLineEdit:focus, LineEdit:focus {
    border: 1px solid #07C160;
    background-color: #363636;
}

/* ComboBox 暗黑样式 */
QComboBox, ComboBox {
    background-color: #2d2d2d;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 6px;
    padding: 6px 12px;
    color: #ffffff;
}

QComboBox:hover, ComboBox:hover {
    border: 1px solid rgba(7, 193, 96, 0.5);
}

QComboBox::drop-down {
    border: none;
    width: 30px;
}

QComboBox QAbstractItemView {
    background-color: #2d2d2d;
    border: 1px solid rgba(255, 255, 255, 0.1);
    selection-background-color: #07C160;
    color: #ffffff;
}

/* 表格暗黑样式 */
QTableWidget, QTableView, TableWidget {
    background-color: #2d2d2d;
    alternate-background-color: #252525;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 8px;
    gridline-color: rgba(255, 255, 255, 0.05);
    color: #ffffff;
}

QTableWidget::item, QTableView::item {
    padding: 8px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

QTableWidget::item:selected, QTableView::item:selected {
    background-color: rgba(7, 193, 96, 0.3);
}

QHeaderView::section {
    background-color: #363636;
    color: #ffffff;
    padding: 10px;
    border: none;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    font-weight: bold;
}

/* 滚动条暗黑样式 */
QScrollBar:vertical {
    background-color: transparent;
    width: 8px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background-color: rgba(255, 255, 255, 0.2);
    border-radius: 4px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background-color: rgba(7, 193, 96, 0.5);
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: none;
}

QScrollBar:horizontal {
    background-color: transparent;
    height: 8px;
    margin: 0;
}

QScrollBar::handle:horizontal {
    background-color: rgba(255, 255, 255, 0.2);
    border-radius: 4px;
    min-width: 30px;
}

QScrollBar::handle:horizontal:hover {
    background-color: rgba(7, 193, 96, 0.5);
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}

/* 标签样式 - 强制透明背景和亮色文字 */
QLabel {
    background-color: transparent;
    background: transparent;
    color: #ffffff;
}

/* qfluentwidgets 标签组件 - 强制亮色文字 */
TitleLabel {
    background-color: transparent;
    color: #ffffff;
    font-weight: bold;
}

BodyLabel {
    background-color: transparent;
    color: #e0e0e0;
}

SubtitleLabel {
    background-color: transparent;
    color: #ffffff;
    font-weight: 600;
}

CaptionLabel {
    background-color: transparent;
    color: #b0b0b0;
}

StrongBodyLabel {
    background-color: transparent;
    color: #ffffff;
    font-weight: bold;
}

LargeTitleLabel {
    background-color: transparent;
    color: #ffffff;
    font-weight: bold;
}

/* 按钮样式 */
QPushButton, PushButton {
    background-color: #363636;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 6px;
    padding: 8px 16px;
    color: #ffffff;
}

QPushButton:hover, PushButton:hover {
    background-color: #404040;
    border: 1px solid rgba(7, 193, 96, 0.5);
}

PrimaryPushButton {
    background-color: #07C160;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    color: #ffffff;
}

PrimaryPushButton:hover {
    background-color: #06AD56;
}

/* SpinBox 样式 */
QSpinBox, SpinBox {
    background-color: #2d2d2d;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 6px;
    padding: 6px 12px;
    color: #ffffff;
}

QSpinBox:focus, SpinBox:focus {
    border: 1px solid #07C160;
}

/* 分隔线 */
QFrame[frameShape="4"], QFrame[frameShape="5"] {
    background-color: rgba(255, 255, 255, 0.08);
}

/* 菜单样式 */
QMenu {
    background-color: #2d2d2d;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    padding: 4px;
}

QMenu::item {
    padding: 8px 20px;
    border-radius: 4px;
    color: #ffffff;
}

QMenu::item:selected {
    background-color: rgba(7, 193, 96, 0.3);
}

/* ToolTip 样式 */
QToolTip {
    background-color: #363636;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 4px;
    padding: 6px 10px;
    color: #ffffff;
}

/* 进度条样式 */
QProgressBar {
    background-color: #2d2d2d;
    border: none;
    border-radius: 4px;
    text-align: center;
    color: #ffffff;
}

QProgressBar::chunk {
    background-color: #07C160;
    border-radius: 4px;
}

/* Switch 开关样式 */
SwitchButton {
    background-color: transparent;
}

/* CheckBox 样式 - 强制透明背景 */
QCheckBox, CheckBox {
    background-color: transparent;
    background: transparent;
    color: #ffffff;
    spacing: 8px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 2px solid rgba(255, 255, 255, 0.3);
    background-color: transparent;
}

QCheckBox::indicator:checked {
    background-color: #07C160;
    border-color: #07C160;
}

QCheckBox::indicator:hover {
    border-color: #07C160;
}

/* RadioButton 样式 */
QRadioButton, RadioButton {
    background-color: transparent;
    background: transparent;
    color: #ffffff;
}

/* GroupBox 样式 */
QGroupBox {
    background-color: transparent;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 8px;
}

QGroupBox::title {
    background-color: transparent;
    color: #ffffff;
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px;
}

/* TextEdit 和 PlainTextEdit 样式 */
QTextEdit, QPlainTextEdit, TextEdit, PlainTextEdit {
    background-color: #2d2d2d;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 6px;
    color: #ffffff;
    padding: 8px;
}

QTextEdit:focus, QPlainTextEdit:focus {
    border: 1px solid #07C160;
}

/* 所有 Widget 内的 QLabel 强制透明 */
QWidget QLabel {
    background: transparent;
    background-color: transparent;
}

/* InfoBar 样式 */
InfoBar {
    background-color: #2d2d2d;
}

/* 确保所有文本类组件透明 */
* {
    selection-background-color: rgba(7, 193, 96, 0.4);
    selection-color: #ffffff;
}
"""


def apply_label_transparent_background(widget):
    """递归地为所有 qfluentwidgets 标签组件设置透明背景
    
    qfluentwidgets 的标签组件在某些情况下会显示不透明的白色背景，
    这在暗黑主题下非常刺眼。本函数通过以下方式解决这个问题：
    
    1. 遍历 widget 及其所有子组件
    2. 识别所有 QLabel 及 qfluentwidgets 的标签类（BodyLabel、TitleLabel 等）
    3. 对每个标签组件应用透明背景设置：
       - 禁用自动填充背景 (setAutoFillBackground)
       - 设置透明背景属性 (WA_TranslucentBackground)
       - 通过调色板设置透明色
       - 追加透明背景的样式表
    
    处理的标签类型包括：
        BodyLabel, TitleLabel, SubtitleLabel, CaptionLabel,
        StrongBodyLabel, LargeTitleLabel, DisplayLabel,
        FluentLabelBase, PixmapLabel
    
    使用时机：
        应在页面创建完成后调用，通常使用 QTimer.singleShot 延迟执行，
        确保所有子组件都已完成初始化。
    
    Args:
        widget: 要处理的根 widget，函数会递归处理其所有子组件
    
    示例:
        >>> from gui.app import apply_label_transparent_background
        >>> # 在主窗口中延迟应用
        >>> QTimer.singleShot(100, lambda: apply_label_transparent_background(self.page))
    """
    from PyQt6.QtWidgets import QLabel, QWidget
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QPalette, QColor
    
    # 需要处理的 qfluentwidgets 标签类名
    label_class_names = {
        'BodyLabel', 'TitleLabel', 'SubtitleLabel', 'CaptionLabel',
        'StrongBodyLabel', 'LargeTitleLabel', 'DisplayLabel',
        'FluentLabelBase', 'PixmapLabel'
    }
    
    def make_transparent(w):
        """强制设置组件背景为透明"""
        # 禁用自动填充背景
        w.setAutoFillBackground(False)
        # 设置透明背景属性
        w.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        w.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        
        # 通过调色板设置透明背景
        palette = w.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(0, 0, 0, 0))
        palette.setColor(QPalette.ColorRole.Base, QColor(0, 0, 0, 0))
        w.setPalette(palette)
        
        # 确保样式表中也设置了透明背景
        current_style = w.styleSheet()
        if 'background' not in current_style.lower():
            w.setStyleSheet(current_style + " background: transparent; background-color: transparent;")
        elif 'transparent' not in current_style.lower():
            # 如果有背景设置但不是透明的，追加透明设置
            w.setStyleSheet(current_style + " background: transparent !important; background-color: transparent !important;")
    
    def process_widget(w):
        class_name = w.__class__.__name__
        
        # 检查是否是 QLabel 或其子类，或者是 qfluentwidgets 的标签类
        if isinstance(w, QLabel) or class_name in label_class_names:
            make_transparent(w)
    
    # 处理根组件
    process_widget(widget)
    
    # 递归处理所有子组件中的 QLabel
    for child in widget.findChildren(QLabel):
        make_transparent(child)
    
    # 额外处理：查找所有 QWidget 子类，检查类名是否匹配
    for child in widget.findChildren(QWidget):
        if child.__class__.__name__ in label_class_names:
            make_transparent(child)


def run_app():
    """运行 GUI 应用程序
    
    这是应用程序的主入口函数，执行以下初始化步骤：
    
    1. 高 DPI 支持配置
       设置 HighDpiScaleFactorRoundingPolicy 为 PassThrough，
       确保在高分辨率显示器上正确缩放。
    
    2. 创建 QApplication 实例
       必须在导入 qfluentwidgets 之前创建，否则会出现初始化错误。
    
    3. 设置应用信息
       - 应用名称: 微信公众号爬虫
       - 版本: 1.0
       - 组织名称: WeChatSpider
    
    4. 配置默认字体
       使用 Microsoft YaHei（微软雅黑）10pt 作为默认字体，
       确保中文显示效果良好。
    
    5. 设置主题
       - 主题模式: 暗黑 (Theme.DARK)
       - 主题色: 微信绿 (#07C160)
    
    6. 应用全局样式表
       加载 DARK_THEME_STYLESHEET，覆盖所有控件的暗黑主题样式。
    
    7. 创建并显示主窗口
       实例化 MainWindow 并调用 show() 显示。
    
    8. 进入事件循环
       调用 app.exec() 进入 Qt 事件循环，程序在此阻塞直到退出。
    
    注意事项:
        - 本函数会调用 sys.exit()，因此调用后不会返回
        - 必须在主线程中调用
        - 不要在 QApplication 创建前导入 qfluentwidgets
    
    示例:
        >>> from gui import run_app
        >>> run_app()  # 启动应用，不会返回
    """
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QFont
    
    # 启用高DPI支持
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    # 创建应用 - 必须在导入qfluentwidgets之前
    app = QApplication(sys.argv)
    
    # 设置应用信息
    app.setApplicationName("微信公众号爬虫")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("WeChatSpider")
    
    # 设置默认字体
    font = QFont("Microsoft YaHei", 10)
    app.setFont(font)
    
    # 现在可以安全导入主窗口了
    from .main_window import MainWindow
    
    # 设置主题
    from qfluentwidgets import setTheme, Theme, setThemeColor
    setTheme(Theme.DARK)
    setThemeColor("#07C160")
    
    # 应用全局暗黑主题样式表
    app.setStyleSheet(DARK_THEME_STYLESHEET)
    
    # 创建主窗口
    window = MainWindow()
    window.show()
    
    # 运行应用
    sys.exit(app.exec())


if __name__ == "__main__":
    run_app()
