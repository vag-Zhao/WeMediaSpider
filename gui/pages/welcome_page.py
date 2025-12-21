#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
欢迎页面 - 微信风格现代化设计

本模块实现了应用程序的欢迎页面，是用户打开应用后看到的第一个页面。
采用微信官方配色方案和卡片式布局，展示应用的核心功能和快速入门指南。

页面结构:
    1. 头部区域: 微信 Logo + 应用标题 + 副标题
    2. 功能卡片区域: 2行3列的功能介绍卡片
    3. 快速开始区域: 使用步骤说明
    4. 底部信息: 版本号和作者信息

自定义组件:
    - WeChatLogoWidget: 微信 Logo 组件，支持远程加载和本地回退
    - GlowingDot: 发光圆点装饰，带呼吸动画效果
    - FeatureIconWidget: 功能图标组件，支持多种图标类型
    - AnimatedFeatureCard: 带悬停动画的功能卡片
    - QuickStartCard: 快速开始卡片

屏幕适配:
    - 小屏幕 (宽度小于1400px): 紧凑布局
    - 中等屏幕 (1400-1600px): 标准布局
    - 大屏幕 (大于1600px): 宽松布局

动画效果:
    - Logo 入场动画（缩放 + 透明度）
    - 发光圆点呼吸动画
    - 卡片悬停上浮动画
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QGraphicsDropShadowEffect, QFrame, QSizePolicy, QApplication, QScrollArea,
    QGridLayout, QSpacerItem
)
from PyQt6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtProperty, 
    QSize, QUrl, QByteArray, QEvent, QParallelAnimationGroup, QSequentialAnimationGroup
)
from PyQt6.QtGui import (
    QPainter, QColor, QLinearGradient, QPainterPath,
    QFont, QBrush, QPen, QPixmap, QRadialGradient, QImage, QCursor
)
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from qfluentwidgets import (
    TitleLabel, SubtitleLabel, BodyLabel, CaptionLabel,
    CardWidget, IconWidget, FluentIcon,
    PrimaryPushButton, PushButton, TransparentPushButton
)


# ==================== 微信官方配色方案 ====================
WECHAT_COLORS = {
    'primary': '#07C160',           # 微信绿 - 主色调
    'primary_dark': '#06AD56',      # 深绿 - 悬停状态
    'primary_light': '#10D070',     # 浅绿 - 高亮状态
    'primary_bg': 'rgba(7, 193, 96, 0.08)',  # 绿色背景
    'primary_bg_hover': 'rgba(7, 193, 96, 0.15)',  # 绿色背景悬停
    
    'white': '#FFFFFF',             # 白色背景
    'bg_light': '#F7F7F7',          # 浅灰背景
    'bg_dark': '#1A1A1A',           # 深色背景（暗色模式）
    'surface': '#2D2D2D',           # 卡片表面色
    'surface_hover': '#363636',     # 卡片悬停色
    
    'text_primary': '#353535',      # 深色文字（亮色模式）
    'text_primary_dark': '#FFFFFF', # 白色文字（暗色模式）
    'text_secondary': '#888888',    # 次要文字
    'text_tertiary': '#B0B0B0',     # 第三级文字
    
    'border': 'rgba(255, 255, 255, 0.08)',  # 边框色
    'border_light': 'rgba(7, 193, 96, 0.2)', # 浅绿边框
    'border_hover': 'rgba(7, 193, 96, 0.5)', # 悬停边框
    
    'shadow': 'rgba(0, 0, 0, 0.1)',  # 阴影色
    'shadow_hover': 'rgba(7, 193, 96, 0.2)',  # 悬停阴影
}


class WeChatLogoWidget(QWidget):
    """微信Logo组件 - 从远程加载官方logo"""
    
    WECHAT_LOGO_URL = "https://res.wx.qq.com/a/wx_fed/assets/res/NTI4MWU5.ico"
    BACKUP_LOGO_URL = "https://www.wechat.com/favicon.ico"
    
    def __init__(self, size=80, parent=None):
        super().__init__(parent)
        self._size = size
        self.setFixedSize(size, size)
        self._opacity = 1.0
        self._scale = 1.0
        self._logo_pixmap = None
        self._loading = True
        self._use_fallback = False
        
        self._network_manager = QNetworkAccessManager(self)
        self._network_manager.finished.connect(self._on_logo_loaded)
        self._load_logo()
        
    def _load_logo(self):
        url = QUrl(self.BACKUP_LOGO_URL if self._use_fallback else self.WECHAT_LOGO_URL)
        request = QNetworkRequest(url)
        request.setRawHeader(b"User-Agent", b"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        self._network_manager.get(request)
        
    def _on_logo_loaded(self, reply: QNetworkReply):
        if reply.error() == QNetworkReply.NetworkError.NoError:
            data = reply.readAll()
            image = QImage()
            if image.loadFromData(data):
                self._logo_pixmap = QPixmap.fromImage(image).scaled(
                    self._size, self._size,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self._loading = False
                self.update()
            elif not self._use_fallback:
                self._use_fallback = True
                self._load_logo()
        elif not self._use_fallback:
            self._use_fallback = True
            self._load_logo()
        else:
            self._loading = False
            self.update()
        reply.deleteLater()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        scaled_size = int(self._size * self._scale)
        offset = (self._size - scaled_size) // 2
        
        painter.setOpacity(self._opacity)
        painter.translate(offset, offset)
        
        if self._logo_pixmap and not self._logo_pixmap.isNull():
            logo_scaled = self._logo_pixmap.scaled(
                scaled_size, scaled_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            x = (scaled_size - logo_scaled.width()) // 2
            y = (scaled_size - logo_scaled.height()) // 2
            painter.drawPixmap(x, y, logo_scaled)
        else:
            self._draw_fallback_logo(painter, scaled_size)
    
    def _draw_fallback_logo(self, painter, scaled_size):
        gradient = QRadialGradient(scaled_size/2, scaled_size/2, scaled_size/2)
        gradient.setColorAt(0, QColor("#1AAD19"))
        gradient.setColorAt(1, QColor("#07C160"))
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(0, 0, scaled_size, scaled_size)
        
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        
        bubble1_x = scaled_size * 0.22
        bubble1_y = scaled_size * 0.28
        bubble1_w = scaled_size * 0.35
        bubble1_h = scaled_size * 0.30
        
        path1 = QPainterPath()
        path1.addEllipse(bubble1_x, bubble1_y, bubble1_w, bubble1_h)
        painter.drawPath(path1)
        
        eye_size = scaled_size * 0.05
        painter.setBrush(QBrush(QColor("#07C160")))
        painter.drawEllipse(int(bubble1_x + bubble1_w * 0.30), int(bubble1_y + bubble1_h * 0.40), int(eye_size), int(eye_size))
        painter.drawEllipse(int(bubble1_x + bubble1_w * 0.55), int(bubble1_y + bubble1_h * 0.40), int(eye_size), int(eye_size))
        
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        bubble2_x = scaled_size * 0.45
        bubble2_y = scaled_size * 0.45
        bubble2_w = scaled_size * 0.32
        bubble2_h = scaled_size * 0.26
        
        path2 = QPainterPath()
        path2.addEllipse(bubble2_x, bubble2_y, bubble2_w, bubble2_h)
        painter.drawPath(path2)
        
        painter.setBrush(QBrush(QColor("#07C160")))
        painter.drawEllipse(int(bubble2_x + bubble2_w * 0.30), int(bubble2_y + bubble2_h * 0.40), int(eye_size), int(eye_size))
        painter.drawEllipse(int(bubble2_x + bubble2_w * 0.55), int(bubble2_y + bubble2_h * 0.40), int(eye_size), int(eye_size))
        
    def get_opacity(self):
        return self._opacity
    
    def set_opacity(self, value):
        self._opacity = value
        self.update()
        
    opacity = pyqtProperty(float, get_opacity, set_opacity)
    
    def get_scale(self):
        return self._scale
    
    def set_scale(self, value):
        self._scale = value
        self.update()
        
    scale = pyqtProperty(float, get_scale, set_scale)


class GlowingDot(QWidget):
    """发光圆点装饰 - 微信风格呼吸动画"""
    
    def __init__(self, color="#07C160", size=8, parent=None):
        super().__init__(parent)
        self._color = QColor(color)
        self._size = size
        self._glow_intensity = 0.5
        self.setFixedSize(size * 3, size * 3)
        
        self._animation = None
        QTimer.singleShot(200, self._start_animation)
    
    def _start_animation(self):
        self._animation = QPropertyAnimation(self, b"glow_intensity")
        self._animation.setDuration(2000)
        self._animation.setStartValue(0.3)
        self._animation.setEndValue(1.0)
        self._animation.setEasingCurve(QEasingCurve.Type.InOutSine)
        self._animation.setLoopCount(-1)
        self._animation.start()
        
    def get_glow_intensity(self):
        return self._glow_intensity
    
    def set_glow_intensity(self, value):
        self._glow_intensity = value
        self.update()
        
    glow_intensity = pyqtProperty(float, get_glow_intensity, set_glow_intensity)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        center_x = self.width() // 2
        center_y = self.height() // 2
        
        glow_color = QColor(self._color)
        glow_color.setAlphaF(0.3 * self._glow_intensity)
        gradient = QRadialGradient(center_x, center_y, self._size * 1.5)
        gradient.setColorAt(0, glow_color)
        gradient.setColorAt(1, QColor(0, 0, 0, 0))
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(center_x - int(self._size * 1.5), center_y - int(self._size * 1.5),
                           int(self._size * 3), int(self._size * 3))
        
        painter.setBrush(QBrush(self._color))
        painter.drawEllipse(center_x - self._size // 2, center_y - self._size // 2,
                           self._size, self._size)


class FeatureIconWidget(QWidget):
    """功能图标组件 - 微信风格渐变图标"""
    
    ICON_TYPES = {
        'login': 'fingerprint',      # 扫码登录
        'scrape': 'download',        # 批量爬取
        'image': 'photo',            # 图片提取
        'result': 'chart',           # 结果查看
        'search': 'search',          # 内容搜索
        'export': 'document',        # 数据导出
    }
    
    def __init__(self, icon_type="login", size=48, parent=None):
        super().__init__(parent)
        self._icon_type = icon_type
        self._size = size
        self._hover = False
        self._scale = 1.0
        self.setFixedSize(size, size)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        size = self._size
        scale = size / 48.0
        
        # 绘制渐变背景
        gradient = QLinearGradient(0, 0, size, size)
        if self._hover:
            gradient.setColorAt(0, QColor("#10D070"))
            gradient.setColorAt(1, QColor("#07C160"))
        else:
            gradient.setColorAt(0, QColor("#07C160"))
            gradient.setColorAt(1, QColor("#06AD56"))
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        radius = int(12 * scale)
        painter.drawRoundedRect(0, 0, size, size, radius, radius)
        
        # 绘制图标
        pen_width = max(1.5, 2 * scale)
        painter.setPen(QPen(QColor(255, 255, 255), pen_width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        
        if self._icon_type == "login":
            # 指纹/扫码图标
            self._draw_fingerprint_icon(painter, scale)
        elif self._icon_type == "scrape":
            # 下载图标
            self._draw_download_icon(painter, scale)
        elif self._icon_type == "image":
            # 图片图标
            self._draw_image_icon(painter, scale)
        elif self._icon_type == "result":
            # 图表图标
            self._draw_chart_icon(painter, scale)
        elif self._icon_type == "search":
            # 搜索图标
            self._draw_search_icon(painter, scale)
        elif self._icon_type == "export":
            # 文档导出图标
            self._draw_export_icon(painter, scale)
    
    def _draw_fingerprint_icon(self, painter, scale):
        # 简化的指纹/扫描框图标
        painter.drawRect(int(12*scale), int(12*scale), int(24*scale), int(24*scale))
        # 四角装饰
        painter.drawLine(int(8*scale), int(16*scale), int(8*scale), int(8*scale))
        painter.drawLine(int(8*scale), int(8*scale), int(16*scale), int(8*scale))
        painter.drawLine(int(32*scale), int(8*scale), int(40*scale), int(8*scale))
        painter.drawLine(int(40*scale), int(8*scale), int(40*scale), int(16*scale))
        painter.drawLine(int(40*scale), int(32*scale), int(40*scale), int(40*scale))
        painter.drawLine(int(40*scale), int(40*scale), int(32*scale), int(40*scale))
        painter.drawLine(int(16*scale), int(40*scale), int(8*scale), int(40*scale))
        painter.drawLine(int(8*scale), int(40*scale), int(8*scale), int(32*scale))
    
    def _draw_download_icon(self, painter, scale):
        # 下载箭头
        painter.drawLine(int(24*scale), int(10*scale), int(24*scale), int(30*scale))
        painter.drawLine(int(16*scale), int(24*scale), int(24*scale), int(32*scale))
        painter.drawLine(int(32*scale), int(24*scale), int(24*scale), int(32*scale))
        # 底部线条
        painter.drawLine(int(12*scale), int(38*scale), int(36*scale), int(38*scale))
    
    def _draw_image_icon(self, painter, scale):
        # 图片框
        painter.drawRoundedRect(int(10*scale), int(12*scale), int(28*scale), int(24*scale), int(3*scale), int(3*scale))
        # 山峰
        path = QPainterPath()
        path.moveTo(int(14*scale), int(30*scale))
        path.lineTo(int(20*scale), int(22*scale))
        path.lineTo(int(26*scale), int(28*scale))
        path.lineTo(int(32*scale), int(20*scale))
        path.lineTo(int(34*scale), int(30*scale))
        painter.drawPath(path)
        # 太阳
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.drawEllipse(int(28*scale), int(16*scale), int(6*scale), int(6*scale))
        painter.setBrush(Qt.BrushStyle.NoBrush)
    
    def _draw_chart_icon(self, painter, scale):
        # 柱状图
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.drawRect(int(12*scale), int(26*scale), int(6*scale), int(12*scale))
        painter.drawRect(int(21*scale), int(18*scale), int(6*scale), int(20*scale))
        painter.drawRect(int(30*scale), int(12*scale), int(6*scale), int(26*scale))
        painter.setBrush(Qt.BrushStyle.NoBrush)
    
    def _draw_search_icon(self, painter, scale):
        # 放大镜
        painter.drawEllipse(int(14*scale), int(12*scale), int(18*scale), int(18*scale))
        painter.drawLine(int(28*scale), int(28*scale), int(36*scale), int(36*scale))
    
    def _draw_export_icon(self, painter, scale):
        # 文档
        painter.drawRect(int(14*scale), int(10*scale), int(20*scale), int(28*scale))
        # 文档线条
        painter.drawLine(int(18*scale), int(18*scale), int(30*scale), int(18*scale))
        painter.drawLine(int(18*scale), int(24*scale), int(30*scale), int(24*scale))
        painter.drawLine(int(18*scale), int(30*scale), int(26*scale), int(30*scale))
    
    def enterEvent(self, event):
        self._hover = True
        self.update()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        self._hover = False
        self.update()
        super().leaveEvent(event)


class AnimatedFeatureCard(CardWidget):
    """带动画效果的功能卡片 - 微信风格"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._hover = False
        self._y_offset = 0
        self._setup_shadow()
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        
    def _setup_shadow(self):
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 40))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)
    
    def get_y_offset(self):
        return self._y_offset
    
    def set_y_offset(self, value):
        self._y_offset = value
        self.update()
    
    y_offset = pyqtProperty(float, get_y_offset, set_y_offset)
        
    def enterEvent(self, event):
        super().enterEvent(event)
        self._hover = True
        shadow = self.graphicsEffect()
        if isinstance(shadow, QGraphicsDropShadowEffect):
            shadow.setBlurRadius(30)
            shadow.setColor(QColor(7, 193, 96, 60))
            shadow.setOffset(0, 8)
        
        # 悬停上浮动画
        self._hover_animation = QPropertyAnimation(self, b"y_offset")
        self._hover_animation.setDuration(200)
        self._hover_animation.setStartValue(0)
        self._hover_animation.setEndValue(-4)
        self._hover_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._hover_animation.start()
            
    def leaveEvent(self, event):
        super().leaveEvent(event)
        self._hover = False
        shadow = self.graphicsEffect()
        if isinstance(shadow, QGraphicsDropShadowEffect):
            shadow.setBlurRadius(20)
            shadow.setColor(QColor(0, 0, 0, 40))
            shadow.setOffset(0, 4)
        
        # 恢复动画
        self._hover_animation = QPropertyAnimation(self, b"y_offset")
        self._hover_animation.setDuration(200)
        self._hover_animation.setStartValue(-4)
        self._hover_animation.setEndValue(0)
        self._hover_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._hover_animation.start()


class QuickStartCard(CardWidget):
    """快速开始卡片 - 微信风格"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_shadow()
        
    def _setup_shadow(self):
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(16)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)


class WelcomePage(QScrollArea):
    """欢迎页面 - 微信风格现代化设计"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("welcomePage")
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setFrameShape(QFrame.Shape.NoFrame)
        
        # 强制设置暗黑背景
        self._apply_dark_background()
        
        self._detect_screen_size()
        
        self._content_widget = QWidget()
        self._content_widget.setObjectName("welcomePageContent")
        self._content_widget.setStyleSheet("background-color: #1a1a1a;")
        self.setWidget(self._content_widget)
        
        self._setup_ui()
        self._start_animations()
    
    def _apply_dark_background(self):
        """强制应用暗黑背景"""
        self.setStyleSheet("""
            QScrollArea#welcomePage {
                background-color: #1a1a1a;
                border: none;
            }
            QScrollArea#welcomePage > QWidget > QWidget {
                background-color: #1a1a1a;
            }
            QWidget#welcomePageContent {
                background-color: #1a1a1a;
            }
        """)
    
    def _detect_screen_size(self):
        screen = QApplication.primaryScreen()
        if screen:
            screen_size = screen.availableGeometry()
            self._screen_width = screen_size.width()
            self._screen_height = screen_size.height()
            self._is_small_screen = self._screen_width < 1600
            self._is_very_small_screen = self._screen_width < 1400
        else:
            self._screen_width = 1920
            self._screen_height = 1080
            self._is_small_screen = False
            self._is_very_small_screen = False
    
    def _get_adaptive_values(self):
        """获取自适应的尺寸值 - 紧凑布局"""
        if self._is_very_small_screen:
            return {
                'margins': (20, 16, 20, 12),
                'logo_size': 66,
                'title_size': 33,
                'subtitle_size': 13,
                'card_height': 140,
                'card_spacing': 10,
                'section_spacing': 14,
                'icon_size': 34,
                'step_num_size': 22,
            }
        elif self._is_small_screen:
            return {
                'margins': (24, 18, 24, 14),
                'logo_size': 64,
                'title_size': 32,
                'subtitle_size': 14,
                'card_height': 150,
                'card_spacing': 12,
                'section_spacing': 16,
                'icon_size': 38,
                'step_num_size': 24,
            }
        else:
            return {
                'margins': (32, 24, 32, 18),
                'logo_size': 72,
                'title_size': 36,
                'subtitle_size': 15,
                'card_height': 160,
                'card_spacing': 14,
                'section_spacing': 20,
                'icon_size': 44,
                'step_num_size': 26,
            }
    
    def _setup_ui(self):
        v = self._get_adaptive_values()
        
        layout = QVBoxLayout(self._content_widget)
        layout.setContentsMargins(*v['margins'])
        layout.setSpacing(0)
        
        # ==================== 头部区域 ====================
        self._setup_header(layout, v)
        layout.addSpacing(v['section_spacing'])
        
        # ==================== 核心功能卡片区域 ====================
        self._setup_feature_cards(layout, v)
        layout.addSpacing(v['section_spacing'])
        
        # ==================== 快速开始区域 ====================
        self._setup_quick_start(layout, v)
        
        layout.addStretch()
        
        # ==================== 底部信息 ====================
        self._setup_footer(layout, v)
    
    def _setup_header(self, layout, v):
        """设置头部区域 - Logo + 标题 - 紧凑设计"""
        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)
        header_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        # 微信Logo
        self.logo_widget = WeChatLogoWidget(size=v['logo_size'])
        header_layout.addWidget(self.logo_widget)
        
        # 标题区域
        title_container = QVBoxLayout()
        title_container.setSpacing(2)
        
        # 主标题
        title = TitleLabel("微信公众号爬虫")
        title.setStyleSheet(f"""
            font-size: {v['title_size']}px;
            font-weight: bold;
            color: {WECHAT_COLORS['text_primary_dark']};
            letter-spacing: 0.5px;
        """)
        title_container.addWidget(title)
        
        # 副标题带装饰
        subtitle_layout = QHBoxLayout()
        subtitle_layout.setSpacing(6)
        subtitle_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        self.glow_dot = GlowingDot(color=WECHAT_COLORS['primary'], size=5)
        subtitle_layout.addWidget(self.glow_dot)
        
        subtitle = SubtitleLabel("高效获取微信公众号文章数据")
        subtitle.setStyleSheet(f"""
            color: {WECHAT_COLORS['primary']};
            font-size: {v['subtitle_size']}px;
            font-weight: 500;
        """)
        subtitle_layout.addWidget(subtitle)
        subtitle_layout.addStretch()
        
        title_container.addLayout(subtitle_layout)
        header_layout.addLayout(title_container)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
    
    def _setup_feature_cards(self, layout, v):
        """设置功能卡片区域 - 2行3列布局"""
        # 功能数据 - 6个核心功能
        features = [
            {
                "icon": "login",
                "title": "扫码登录",
                "desc": "使用微信扫描二维码完成登录，安全快捷获取访问权限",
                "number": "01"
            },
            {
                "icon": "scrape", 
                "title": "批量爬取",
                "desc": "支持多个公众号同时爬取，自定义日期范围和页数限制",
                "number": "02"
            },
            {
                "icon": "image",
                "title": "图片提取",
                "desc": "从文章中提取所有图片，保存为Markdown文档和图片文件",
                "number": "03"
            },
            {
                "icon": "result",
                "title": "结果查看",
                "desc": "实时预览爬取结果，支持筛选、排序和数据统计分析",
                "number": "04"
            },
            {
                "icon": "search",
                "title": "内容搜索",
                "desc": "支持正则表达式搜索，快速定位目标内容和关键信息",
                "number": "05"
            },
            {
                "icon": "export",
                "title": "数据导出",
                "desc": "支持CSV、Excel、HTML等多种格式导出完整数据",
                "number": "06"
            }
        ]
        
        # 使用网格布局 - 2行3列
        grid_layout = QGridLayout()
        grid_layout.setSpacing(v['card_spacing'])
        
        self.feature_cards = []
        for i, feature in enumerate(features):
            row = i // 3
            col = i % 3
            card = self._create_feature_card(feature, v)
            grid_layout.addWidget(card, row, col)
            self.feature_cards.append(card)
        
        layout.addLayout(grid_layout)
    
    def _create_feature_card(self, feature, v):
        """创建单个功能卡片 - 紧凑设计"""
        card = AnimatedFeatureCard(self._content_widget)
        card.setFixedHeight(v['card_height'])
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        card.setStyleSheet(f"""
            AnimatedFeatureCard {{
                background-color: {WECHAT_COLORS['surface']};
                border: 1px solid {WECHAT_COLORS['border_light']};
                border-radius: 12px;
            }}
            AnimatedFeatureCard:hover {{
                border: 1px solid {WECHAT_COLORS['border_hover']};
                background-color: {WECHAT_COLORS['surface_hover']};
            }}
        """)
        
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(14, 12, 14, 12)
        card_layout.setSpacing(6)
        
        # 顶部：图标 + 编号
        top_layout = QHBoxLayout()
        top_layout.setSpacing(0)
        
        icon_widget = FeatureIconWidget(feature["icon"], size=v['icon_size'])
        top_layout.addWidget(icon_widget)
        top_layout.addStretch()
        
        # 装饰性编号
        num_label = QLabel(feature["number"])
        num_label.setStyleSheet(f"""
            color: rgba(7, 193, 96, 0.2);
            font-size: {v['icon_size'] - 6}px;
            font-weight: bold;
        """)
        top_layout.addWidget(num_label)
        
        card_layout.addLayout(top_layout)
        
        # 标题
        title_label = SubtitleLabel(feature["title"])
        title_label.setStyleSheet(f"""
            font-size: {12 if self._is_small_screen else 14}px;
            font-weight: bold;
            color: {WECHAT_COLORS['text_primary_dark']};
        """)
        card_layout.addWidget(title_label)
        
        # 描述 - 单行显示
        desc_label = BodyLabel(feature["desc"])
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet(f"""
            color: {WECHAT_COLORS['text_secondary']};
            font-size: {10 if self._is_small_screen else 11}px;
            line-height: 1.3;
        """)
        card_layout.addWidget(desc_label)
        
        card_layout.addStretch()
        
        return card
    
    def _setup_quick_start(self, layout, v):
        """设置快速开始区域 - 单列垂直布局，详细说明"""
        quick_card = QuickStartCard(self._content_widget)
        quick_card.setStyleSheet(f"""
            QuickStartCard {{
                background-color: {WECHAT_COLORS['surface']};
                border: 1px solid {WECHAT_COLORS['border_light']};
                border-radius: 12px;
            }}
        """)
        
        card_layout = QVBoxLayout(quick_card)
        card_layout.setContentsMargins(18, 14, 18, 14)
        card_layout.setSpacing(10)
        
        # 标题行
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)
        
        tip_icon = GlowingDot(color=WECHAT_COLORS['primary'], size=6)
        header_layout.addWidget(tip_icon)
        
        tip_title = SubtitleLabel("快速开始")
        tip_title.setStyleSheet(f"""
            font-size: {13 if self._is_small_screen else 15}px;
            font-weight: bold;
            color: {WECHAT_COLORS['text_primary_dark']};
        """)
        header_layout.addWidget(tip_title)
        header_layout.addStretch()
        
        card_layout.addLayout(header_layout)
        
        # 分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet(f"background-color: {WECHAT_COLORS['border_light']};")
        separator.setFixedHeight(1)
        card_layout.addWidget(separator)
        
        # 步骤列表 - 单列垂直布局，详细说明
        steps = [
            ("01", "点击左侧「账号登录」进行微信扫码登录"),
            ("02", "登录成功后，进入「公众号爬取」页面"),
            ("03", "输入要爬取的公众号名称，设置参数后开始爬取"),
            ("04", "爬取完成后可在「结果查看」页面查看和导出数据"),
            ("05", "程序还存在一些未被发现的bug，欢迎反馈！"),
            ("06", "在微信中，可以通过点击公众号文章界面的右上角的  · · ·  实现复制文章链接")
        ]
        
        
        steps_container = QVBoxLayout()
        steps_container.setSpacing(6)
        steps_container.setContentsMargins(0, 0, 0, 0)
        
        for num, text in steps:
            step_layout = QHBoxLayout()
            step_layout.setContentsMargins(0, 0, 0, 0)
            step_layout.setSpacing(10)
            
            # 步骤编号
            num_label = QLabel(num)
            num_label.setFixedSize(v['step_num_size'], v['step_num_size'])
            num_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            num_label.setStyleSheet(f"""
                background-color: {WECHAT_COLORS['primary_bg']};
                color: {WECHAT_COLORS['primary']};
                font-size: {10 if self._is_small_screen else 11}px;
                font-weight: bold;
                border-radius: {v['step_num_size'] // 4}px;
            """)
            step_layout.addWidget(num_label)
            
            # 步骤文字
            step_label = BodyLabel(text)
            step_label.setStyleSheet(f"""
                color: {WECHAT_COLORS['text_tertiary']};
                font-size: {11 if self._is_small_screen else 12}px;
                background-color: transparent;
            """)
            step_layout.addWidget(step_label)
            step_layout.addStretch()
            
            steps_container.addLayout(step_layout)
        
        card_layout.addLayout(steps_container)
        layout.addWidget(quick_card)
    
    def _setup_footer(self, layout, v):
        """设置底部信息 - 紧凑设计"""
        layout.addSpacing(8)
        
        footer_layout = QHBoxLayout()
        footer_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        version_container = QHBoxLayout()
        version_container.setSpacing(6)
        
        font_size = 10 if self._is_small_screen else 11
        
        powered_label = BodyLabel("Powered by")
        powered_label.setStyleSheet(f"color: #555; font-size: {font_size}px;")
        version_container.addWidget(powered_label)
        
        author_label = BodyLabel("Vag - Zhao")
        author_label.setStyleSheet(f"color: {WECHAT_COLORS['primary']}; font-size: {font_size}px; font-weight: bold;")
        version_container.addWidget(author_label)
        
        divider = BodyLabel("•")
        divider.setStyleSheet(f"color: #555; font-size: {font_size}px;")
        version_container.addWidget(divider)
        
        version_label = BodyLabel("v1.0.0")
        version_label.setStyleSheet(f"color: #555; font-size: {font_size}px;")
        version_container.addWidget(version_label)
        
        footer_layout.addLayout(version_container)
        layout.addLayout(footer_layout)
    
    def _start_animations(self):
        """启动入场动画"""
        # Logo缩放动画
        self.logo_animation = QPropertyAnimation(self.logo_widget, b"scale")
        self.logo_animation.setDuration(800)
        self.logo_animation.setStartValue(0.5)
        self.logo_animation.setEndValue(1.0)
        self.logo_animation.setEasingCurve(QEasingCurve.Type.OutBack)
        
        # Logo透明度动画
        self.logo_opacity_animation = QPropertyAnimation(self.logo_widget, b"opacity")
        self.logo_opacity_animation.setDuration(600)
        self.logo_opacity_animation.setStartValue(0.0)
        self.logo_opacity_animation.setEndValue(1.0)
        self.logo_opacity_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # 启动动画
        QTimer.singleShot(100, self.logo_animation.start)
        QTimer.singleShot(100, self.logo_opacity_animation.start)