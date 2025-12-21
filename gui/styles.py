#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
全局样式定义 - 微信风格现代化设计系统

本模块定义了应用程序的全局样式，采用微信官方配色方案，
实现了一套完整的暗黑主题设计系统。

配色方案:
    主色调: 微信绿 (#07C160)
    背景色: 深灰 (#1A1A1A)
    表面色: 中灰 (#2D2D2D)
    文字色: 白色/灰色渐变

设计原则:
    1. 一致性: 所有组件使用统一的配色和圆角
    2. 层次感: 通过背景色深浅区分不同层级
    3. 交互反馈: 悬停和点击状态有明显的视觉变化
    4. 可读性: 文字颜色与背景有足够的对比度

模块内容:
    - WECHAT_COLORS: 微信官方配色字典
    - COLORS: 简化的主题颜色字典
    - CARD_STYLES: 卡片组件样式
    - BUTTON_STYLES: 按钮组件样式
    - INPUT_STYLES: 输入框样式
    - LABEL_STYLES: 标签样式
    - ANIMATION_DURATION: 动画时长配置
    - SHADOW_CONFIG: 阴影配置
    - 各种样式获取函数
"""

# ==================== 微信官方配色方案 ====================
WECHAT_COLORS = {
    # 主色调
    'primary': '#07C160',           # 微信绿 - 主色调
    'primary_dark': '#06AD56',      # 深绿 - 悬停状态
    'primary_light': '#10D070',     # 浅绿 - 高亮状态
    'primary_bg': 'rgba(7, 193, 96, 0.08)',  # 绿色背景
    'primary_bg_hover': 'rgba(7, 193, 96, 0.15)',  # 绿色背景悬停
    
    # 辅助色
    'secondary': '#576B95',         # 微信蓝 - 链接色
    'secondary_dark': '#4A5B7E',    # 深蓝
    
    # 背景色
    'white': '#FFFFFF',             # 白色背景
    'bg_light': '#F7F7F7',          # 浅灰背景（亮色模式）
    'bg_dark': '#1A1A1A',           # 深色背景（暗色模式）
    'surface': '#2D2D2D',           # 卡片表面色
    'surface_hover': '#363636',     # 卡片悬停色
    
    # 文字色
    'text_primary': '#353535',      # 深色文字（亮色模式）
    'text_primary_dark': '#FFFFFF', # 白色文字（暗色模式）
    'text_secondary': '#888888',    # 次要文字
    'text_tertiary': '#B0B0B0',     # 第三级文字
    
    # 边框色
    'border': 'rgba(255, 255, 255, 0.08)',  # 边框色
    'border_light': 'rgba(7, 193, 96, 0.2)', # 浅绿边框
    'border_hover': 'rgba(7, 193, 96, 0.5)', # 悬停边框
}

# 主题颜色（用于自定义组件）
COLORS = {
    'primary': '#07C160',
    'primary_dark': '#06AD56',
    'primary_light': '#10D070',
    'secondary': '#5B9BD5',
    'background': '#1A1A1A',
    'surface': '#2D2D2D',
    'surface_light': '#363636',
    'text': '#FFFFFF',
    'text_secondary': '#888888',
    'text_tertiary': '#B0B0B0',
    'border': 'rgba(255, 255, 255, 0.08)',
    'border_light': 'rgba(7, 193, 96, 0.2)',
    'error': '#FA5151',
    'warning': '#FFC300',
    'success': '#07C160',
}

# 卡片样式
CARD_STYLES = {
    'default': """
        background-color: rgba(45, 45, 45, 0.9);
        border: 1px solid rgba(7, 193, 96, 0.2);
        border-radius: 16px;
    """,
    'hover': """
        border: 1px solid rgba(7, 193, 96, 0.5);
        background-color: rgba(50, 50, 50, 0.95);
    """,
    'active': """
        border: 1px solid #07C160;
        background-color: rgba(7, 193, 96, 0.1);
    """
}

# 按钮样式
BUTTON_STYLES = {
    'primary': """
        QPushButton {
            background-color: #07C160;
            color: white;
            border: none;
            border-radius: 8px;
            padding: 10px 24px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #06AD56;
        }
        QPushButton:pressed {
            background-color: #059B4D;
        }
    """,
    'secondary': """
        QPushButton {
            background-color: transparent;
            color: #07C160;
            border: 1px solid #07C160;
            border-radius: 8px;
            padding: 10px 24px;
        }
        QPushButton:hover {
            background-color: rgba(7, 193, 96, 0.1);
        }
    """
}

# 输入框样式
INPUT_STYLES = """
    QLineEdit, QTextEdit {
        background-color: rgba(45, 45, 45, 0.8);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 8px;
        padding: 8px 12px;
        color: #E0E0E0;
    }
    QLineEdit:focus, QTextEdit:focus {
        border: 1px solid #07C160;
        background-color: rgba(45, 45, 45, 0.95);
    }
"""

# 标签样式
LABEL_STYLES = {
    'title': """
        font-size: 32px;
        font-weight: bold;
        color: #FFFFFF;
    """,
    'subtitle': """
        font-size: 16px;
        color: #07C160;
        font-weight: 500;
    """,
    'body': """
        font-size: 14px;
        color: #B0B0B0;
    """,
    'caption': """
        font-size: 12px;
        color: #666666;
    """
}

# 动画时长配置
ANIMATION_DURATION = {
    'fast': 150,
    'normal': 300,
    'slow': 500,
    'very_slow': 800
}

# 阴影配置
SHADOW_CONFIG = {
    'small': {
        'blur': 10,
        'color': (0, 0, 0, 40),
        'offset': (0, 2)
    },
    'medium': {
        'blur': 20,
        'color': (0, 0, 0, 60),
        'offset': (0, 4)
    },
    'large': {
        'blur': 30,
        'color': (0, 0, 0, 80),
        'offset': (0, 8)
    },
    'glow': {
        'blur': 30,
        'color': (7, 193, 96, 80),
        'offset': (0, 6)
    }
}


def setup_theme():
    """设置 Fluent 主题
    
    配置 qfluentwidgets 的主题为暗黑模式，并设置主题色为微信绿。
    
    注意:
        必须在 QApplication 创建后调用，否则会报错。
        通常在 run_app() 中已经调用，不需要手动调用。
    """
    from qfluentwidgets import setTheme, Theme, setThemeColor
    from PyQt6.QtGui import QColor
    setTheme(Theme.DARK)
    setThemeColor(QColor("#07C160"))


def get_welcome_page_style():
    """获取欢迎页面的完整样式表
    
    返回欢迎页面专用的 QSS 样式表，包含：
    - 页面背景色
    - 滚动条样式
    - 卡片组件样式
    - 标题和正文标签样式
    
    Returns:
        完整的 QSS 样式表字符串
    """
    return """
        #welcomePage {
            background-color: #1a1a1a;
            border: none;
        }
        
        /* 滚动条样式 */
        QScrollArea {
            border: none;
            background-color: transparent;
        }
        
        QScrollBar:vertical {
            background-color: transparent;
            width: 8px;
            margin: 0;
        }
        
        QScrollBar::handle:vertical {
            background-color: rgba(7, 193, 96, 0.3);
            border-radius: 4px;
            min-height: 30px;
        }
        
        QScrollBar::handle:vertical:hover {
            background-color: rgba(7, 193, 96, 0.5);
        }
        
        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical {
            height: 0;
        }
        
        QScrollBar::add-page:vertical,
        QScrollBar::sub-page:vertical {
            background: none;
        }
        
        /* 卡片基础样式 */
        CardWidget {
            background-color: #2D2D2D;
            border: 1px solid rgba(7, 193, 96, 0.2);
            border-radius: 16px;
        }
        
        CardWidget:hover {
            border: 1px solid rgba(7, 193, 96, 0.5);
            background-color: #363636;
        }
        
        /* 功能卡片样式 */
        AnimatedFeatureCard {
            background-color: #2D2D2D;
            border: 1px solid rgba(7, 193, 96, 0.2);
            border-radius: 16px;
        }
        
        AnimatedFeatureCard:hover {
            border: 1px solid rgba(7, 193, 96, 0.5);
            background-color: #363636;
        }
        
        /* 快速开始卡片样式 */
        QuickStartCard {
            background-color: #2D2D2D;
            border: 1px solid rgba(7, 193, 96, 0.2);
            border-radius: 16px;
        }
        
        /* 标题样式 */
        TitleLabel {
            font-size: 34px;
            font-weight: bold;
            color: #FFFFFF;
            letter-spacing: 1px;
        }
        
        SubtitleLabel {
            font-size: 15px;
            color: #07C160;
            font-weight: 500;
        }
        
        BodyLabel {
            font-size: 13px;
            color: #888888;
            line-height: 1.5;
        }
        
        CaptionLabel {
            font-size: 12px;
            color: #B0B0B0;
        }
    """


def get_card_hover_style():
    """获取卡片悬停状态的样式
    
    Returns:
        卡片悬停时的 CSS 样式字符串，包含边框和背景色变化
    """
    return """
        border: 1px solid rgba(7, 193, 96, 0.5);
        background-color: #363636;
    """


def get_primary_button_style():
    """获取主要按钮的样式表
    
    主要按钮使用微信绿作为背景色，适用于主要操作按钮。
    包含正常、悬停、按下和禁用四种状态的样式。
    
    Returns:
        QPushButton 的完整 QSS 样式表
    """
    return """
        QPushButton {
            background-color: #07C160;
            color: white;
            border: none;
            border-radius: 8px;
            padding: 10px 24px;
            font-weight: bold;
            font-size: 14px;
        }
        QPushButton:hover {
            background-color: #06AD56;
        }
        QPushButton:pressed {
            background-color: #059B4D;
        }
        QPushButton:disabled {
            background-color: #3D3D3D;
            color: #666666;
        }
    """


def get_secondary_button_style():
    """获取次要按钮的样式表
    
    次要按钮使用透明背景和绿色边框，适用于次要操作按钮。
    包含正常、悬停和按下三种状态的样式。
    
    Returns:
        QPushButton 的完整 QSS 样式表
    """
    return """
        QPushButton {
            background-color: transparent;
            color: #07C160;
            border: 1px solid #07C160;
            border-radius: 8px;
            padding: 10px 24px;
            font-size: 14px;
        }
        QPushButton:hover {
            background-color: rgba(7, 193, 96, 0.1);
        }
        QPushButton:pressed {
            background-color: rgba(7, 193, 96, 0.2);
        }
    """
