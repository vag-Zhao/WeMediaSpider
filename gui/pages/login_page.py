#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
登录页面 - 状态显示与内嵌浏览器登录

本模块实现了微信公众平台的登录功能，采用内嵌浏览器方式，
用户无需离开应用即可完成扫码登录。

主要功能:
    1. 登录状态显示: 显示当前登录状态、登录时间和过期时间
    2. 扫码登录: 内嵌 QWebEngineView 加载微信公众平台登录页
    3. 凭证导出: 将登录信息编码为可分享的字符串
    4. 凭证导入: 从分享的字符串恢复登录状态
    5. 缓存管理: 清除登录缓存

页面结构:
    使用 QStackedWidget 在两个视图间切换：
    - 状态视图: 显示登录状态和操作按钮
    - 浏览器视图: 内嵌浏览器进行扫码登录

自定义组件:
    - StatusIndicator: 带发光效果的状态指示灯
    - CookieCollector: Cookie 收集器，监听浏览器 Cookie
    - CustomWebEnginePage: 自定义页面，拦截新窗口请求
    - ImportCredentialDialog: 凭证导入对话框

登录流程:
    1. 用户点击"扫码登录"按钮
    2. 切换到浏览器视图，加载微信公众平台
    3. 用户使用微信扫码登录
    4. 监听 URL 变化，检测登录成功（URL 中包含 token）
    5. 收集 Cookie 并保存到本地缓存
    6. 切换回状态视图，显示登录成功

凭证分享机制:
    使用 spider.wechat.cache_codec 模块对缓存文件进行编码/解码，
    生成的字符串以 "WC01" 开头，包含版本号、校验和等信息。
"""

import re
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QStackedWidget,
    QDialog, QTextEdit, QApplication
)
from PyQt6.QtCore import pyqtSignal, QUrl, QTimer, Qt, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QRadialGradient
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEnginePage

from qfluentwidgets import (
    ScrollArea, TitleLabel, BodyLabel, CaptionLabel, SubtitleLabel,
    PrimaryPushButton, PushButton, CardWidget,
    InfoBar, InfoBarPosition, FluentIcon, ProgressRing,
    MessageBox, PlainTextEdit
)

from ..styles import COLORS
from ..utils import play_sound
from spider.wechat.login import WeChatSpiderLogin
from spider.wechat.cache_codec import (
    encode_cache_file, decode_to_cache_file,
    validate_encoded_string, get_cache_info,
    CacheCodecError, DecodeError, ValidationError, ChecksumError, VersionError
)


class StatusIndicator(QWidget):
    """美观的状态指示器 - 带发光效果的圆形指示灯"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(28, 28)
        self._is_active = False
        self._glow_opacity = 0.0
        self._pulse_scale = 1.0
        
        # 发光动画
        self._glow_animation = QPropertyAnimation(self, b"glowOpacity")
        self._glow_animation.setDuration(1500)
        self._glow_animation.setLoopCount(-1)  # 无限循环
        self._glow_animation.setEasingCurve(QEasingCurve.Type.InOutSine)
        
        # 脉冲动画
        self._pulse_animation = QPropertyAnimation(self, b"pulseScale")
        self._pulse_animation.setDuration(1500)
        self._pulse_animation.setLoopCount(-1)
        self._pulse_animation.setEasingCurve(QEasingCurve.Type.InOutSine)
    
    def get_glow_opacity(self):
        return self._glow_opacity
    
    def set_glow_opacity(self, value):
        self._glow_opacity = value
        self.update()
    
    def get_pulse_scale(self):
        return self._pulse_scale
    
    def set_pulse_scale(self, value):
        self._pulse_scale = value
        self.update()
    
    glowOpacity = pyqtProperty(float, get_glow_opacity, set_glow_opacity)
    pulseScale = pyqtProperty(float, get_pulse_scale, set_pulse_scale)
    
    def setActive(self, active: bool):
        """设置激活状态"""
        self._is_active = active
        
        if active:
            # 启动动画
            self._glow_animation.setStartValue(0.3)
            self._glow_animation.setEndValue(0.8)
            self._glow_animation.start()
            
            self._pulse_animation.setStartValue(0.9)
            self._pulse_animation.setEndValue(1.1)
            self._pulse_animation.start()
        else:
            # 停止动画
            self._glow_animation.stop()
            self._pulse_animation.stop()
            self._glow_opacity = 0.0
            self._pulse_scale = 1.0
        
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        center_x = self.width() / 2
        center_y = self.height() / 2
        
        if self._is_active:
            # 已登录 - 绿色发光效果
            base_color = QColor("#07C160")  # 微信绿
            
            # 外层发光
            if self._glow_opacity > 0:
                glow_radius = 12 * self._pulse_scale
                glow_gradient = QRadialGradient(center_x, center_y, glow_radius)
                glow_color = QColor(base_color)
                glow_color.setAlphaF(self._glow_opacity * 0.4)
                glow_gradient.setColorAt(0, glow_color)
                glow_color.setAlphaF(0)
                glow_gradient.setColorAt(1, glow_color)
                painter.setBrush(QBrush(glow_gradient))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(int(center_x - glow_radius), int(center_y - glow_radius),
                                   int(glow_radius * 2), int(glow_radius * 2))
            
            # 中间光晕
            mid_radius = 8
            mid_gradient = QRadialGradient(center_x, center_y, mid_radius)
            mid_color = QColor(base_color)
            mid_color.setAlphaF(0.3)
            mid_gradient.setColorAt(0, mid_color)
            mid_color.setAlphaF(0.1)
            mid_gradient.setColorAt(1, mid_color)
            painter.setBrush(QBrush(mid_gradient))
            painter.drawEllipse(int(center_x - mid_radius), int(center_y - mid_radius),
                               int(mid_radius * 2), int(mid_radius * 2))
            
            # 核心圆点
            core_radius = 5
            core_gradient = QRadialGradient(center_x - 1, center_y - 1, core_radius)
            core_gradient.setColorAt(0, QColor("#4ADE80"))  # 亮绿
            core_gradient.setColorAt(0.7, base_color)
            core_gradient.setColorAt(1, QColor("#059669"))  # 深绿
            painter.setBrush(QBrush(core_gradient))
            painter.setPen(QPen(QColor("#059669"), 1))
            painter.drawEllipse(int(center_x - core_radius), int(center_y - core_radius),
                               int(core_radius * 2), int(core_radius * 2))
            
            # 高光点
            highlight_radius = 1.5
            painter.setBrush(QBrush(QColor(255, 255, 255, 180)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(int(center_x - 2), int(center_y - 2),
                               int(highlight_radius * 2), int(highlight_radius * 2))
        else:
            # 未登录 - 灰色/红色暗淡效果
            base_color = QColor("#6B7280")  # 灰色
            
            # 外圈
            outer_radius = 8
            painter.setBrush(QBrush(QColor(60, 60, 60, 100)))
            painter.setPen(QPen(QColor(80, 80, 80), 1))
            painter.drawEllipse(int(center_x - outer_radius), int(center_y - outer_radius),
                               int(outer_radius * 2), int(outer_radius * 2))
            
            # 核心圆点 - 暗红色
            core_radius = 4
            core_gradient = QRadialGradient(center_x - 0.5, center_y - 0.5, core_radius)
            core_gradient.setColorAt(0, QColor("#9CA3AF"))  # 浅灰
            core_gradient.setColorAt(0.5, QColor("#6B7280"))  # 中灰
            core_gradient.setColorAt(1, QColor("#4B5563"))  # 深灰
            painter.setBrush(QBrush(core_gradient))
            painter.setPen(QPen(QColor("#4B5563"), 0.5))
            painter.drawEllipse(int(center_x - core_radius), int(center_y - core_radius),
                               int(core_radius * 2), int(core_radius * 2))


class CookieCollector:
    """Cookie收集器"""
    def __init__(self):
        self.cookies = {}
    
    def on_cookie_added(self, cookie):
        name = cookie.name().data().decode()
        value = cookie.value().data().decode()
        domain = cookie.domain()
        if 'weixin' in domain or 'qq.com' in domain:
            self.cookies[name] = value
    
    def clear(self):
        self.cookies = {}


class CustomWebEnginePage(QWebEnginePage):
    """自定义WebEnginePage，拦截新窗口请求"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
    
    def createWindow(self, window_type):
        """
        重写createWindow方法，拦截所有新窗口请求
        将新窗口请求重定向到当前页面，防止打开外部浏览器
        """
        # 返回当前页面，使链接在当前页面打开
        return self
    
    def acceptNavigationRequest(self, url, nav_type, is_main_frame):
        """
        接受所有导航请求，确保页面正常加载
        """
        return True


class ImportCredentialDialog(QDialog):
    """
    导入凭证对话框
    
    提供一个文本输入区域，让用户粘贴分享的凭证字符串，
    并进行验证和导入操作。
    """
    
    # 导入成功信号
    import_success = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("导入登录凭证")
        self.setMinimumSize(500, 350)
        self.setModal(True)
        
        # 设置暗色主题样式
        self.setStyleSheet("""
            QDialog {
                background-color: #2d2d2d;
                color: white;
            }
            QLabel {
                color: white;
            }
        """)
        
        self._setup_ui()
    
    def _setup_ui(self):
        """设置对话框UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # 标题
        title = SubtitleLabel("导入登录凭证")
        title.setStyleSheet("color: white; font-size: 16px; background-color: transparent;")
        layout.addWidget(title)
        
        # 说明文字
        desc = BodyLabel("请将分享的凭证字符串粘贴到下方输入框中：")
        desc.setStyleSheet("color: #aaa; background-color: transparent;")
        layout.addWidget(desc)
        
        # 输入框
        self.input_edit = PlainTextEdit()
        self.input_edit.setPlaceholderText("粘贴凭证字符串（以 WC01 开头）...")
        self.input_edit.setMinimumHeight(120)
        self.input_edit.setStyleSheet("""
            PlainTextEdit {
                background-color: #1a1a1a;
                border: 1px solid #404040;
                border-radius: 6px;
                color: white;
                padding: 8px;
                font-family: Consolas, Monaco, monospace;
                font-size: 12px;
            }
            PlainTextEdit:focus {
                border-color: #07C160;
            }
        """)
        layout.addWidget(self.input_edit)
        
        # 状态提示
        self.status_label = CaptionLabel("")
        self.status_label.setStyleSheet("color: #888; background-color: transparent;")
        layout.addWidget(self.status_label)
        
        # 按钮区域
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        
        # 从剪贴板粘贴按钮
        self.paste_btn = PushButton("从剪贴板粘贴", icon=FluentIcon.PASTE)
        self.paste_btn.clicked.connect(self._on_paste_clicked)
        btn_layout.addWidget(self.paste_btn)
        
        # 验证按钮
        self.validate_btn = PushButton("验证", icon=FluentIcon.CHECKBOX)
        self.validate_btn.clicked.connect(self._on_validate_clicked)
        btn_layout.addWidget(self.validate_btn)
        
        btn_layout.addStretch()
        
        # 取消按钮
        self.cancel_btn = PushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)
        
        # 导入按钮
        self.import_btn = PrimaryPushButton("导入", icon=FluentIcon.DOWNLOAD)
        self.import_btn.clicked.connect(self._on_import_clicked)
        btn_layout.addWidget(self.import_btn)
        
        layout.addLayout(btn_layout)
        
        # 提示信息
        tips = CaptionLabel("提示：导入后将覆盖当前的登录信息，原有登录状态会自动备份")
        tips.setStyleSheet("color: #666; background-color: transparent;")
        layout.addWidget(tips)
    
    def _on_paste_clicked(self):
        """从剪贴板粘贴"""
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        if text:
            self.input_edit.setPlainText(text.strip())
            self._update_status("已从剪贴板粘贴", "#07C160")
        else:
            self._update_status("剪贴板为空", "#ff6b6b")
    
    def _on_validate_clicked(self):
        """验证凭证字符串"""
        text = self.input_edit.toPlainText().strip()
        
        if not text:
            self._update_status("请输入凭证字符串", "#ff6b6b")
            return
        
        is_valid, message = validate_encoded_string(text)
        
        if is_valid:
            self._update_status(f"✓ {message}", "#07C160")
        else:
            self._update_status(f"✗ {message}", "#ff6b6b")
    
    def _on_import_clicked(self):
        """执行导入操作"""
        text = self.input_edit.toPlainText().strip()
        
        if not text:
            self._update_status("请输入凭证字符串", "#ff6b6b")
            return
        
        # 先验证
        is_valid, message = validate_encoded_string(text)
        if not is_valid:
            self._update_status(f"✗ {message}", "#ff6b6b")
            return
        
        try:
            # 执行解码和写入
            data = decode_to_cache_file(text, backup=True)
            info = get_cache_info(data)
            
            self._update_status(
                f"✓ 导入成功！Token: {info['token_preview']}, "
                f"Cookie数量: {info['cookie_count']}",
                "#07C160"
            )
            
            # 发送成功信号
            self.import_success.emit()
            
            # 延迟关闭对话框
            QTimer.singleShot(1500, self.accept)
            
        except ChecksumError as e:
            self._update_status(f"✗ 数据校验失败：凭证可能已损坏", "#ff6b6b")
        except VersionError as e:
            self._update_status(f"✗ 版本不兼容：{str(e)}", "#ff6b6b")
        except ValidationError as e:
            self._update_status(f"✗ 数据格式错误：{str(e)}", "#ff6b6b")
        except DecodeError as e:
            self._update_status(f"✗ 解码失败：{str(e)}", "#ff6b6b")
        except Exception as e:
            self._update_status(f"✗ 导入失败：{str(e)}", "#ff6b6b")
    
    def _update_status(self, message: str, color: str):
        """更新状态提示"""
        self.status_label.setText(message)
        self.status_label.setStyleSheet(f"color: {color}; background-color: transparent;")


class LoginPage(QWidget):
    """登录页面 - 状态显示与内嵌浏览器登录"""
    
    login_status_changed = pyqtSignal(bool)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.login_manager = WeChatSpiderLogin()
        self.cookie_collector = CookieCollector()
        self.setObjectName("loginPage")
        
        # 强制设置暗黑背景
        self.setStyleSheet("background-color: #1a1a1a;")
        
        self._setup_ui()
        self._setup_cookie_listener()
        self._check_login_status()
    
    def _setup_cookie_listener(self):
        """设置Cookie监听器"""
        profile = QWebEngineProfile.defaultProfile()
        cookie_store = profile.cookieStore()
        cookie_store.cookieAdded.connect(self.cookie_collector.on_cookie_added)
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 使用 QStackedWidget 切换状态视图和浏览器视图
        self.stacked_widget = QStackedWidget()
        layout.addWidget(self.stacked_widget)
        
        # 创建状态视图（原有的登录状态页面）
        self.status_view = self._create_status_view()
        self.stacked_widget.addWidget(self.status_view)
        
        # 创建浏览器视图（内嵌浏览器）
        self.browser_view = self._create_browser_view()
        self.stacked_widget.addWidget(self.browser_view)
        
        # 默认显示状态视图
        self.stacked_widget.setCurrentWidget(self.status_view)
    
    def _create_status_view(self):
        """创建状态视图"""
        status_widget = QWidget()
        
        page = ScrollArea()
        page.setWidgetResizable(True)
        
        container = QWidget()
        page.setWidget(container)
        
        content_layout = QVBoxLayout(container)
        content_layout.setContentsMargins(36, 20, 36, 36)
        content_layout.setSpacing(20)
        
        title = TitleLabel("账号登录")
        content_layout.addWidget(title)
        
        # 登录状态卡片
        status_card = CardWidget()
        status_layout = QVBoxLayout(status_card)
        status_layout.setContentsMargins(24, 24, 24, 24)
        status_layout.setSpacing(16)
        
        header_layout = QHBoxLayout()
        status_title = SubtitleLabel("登录状态")
        header_layout.addWidget(status_title)
        header_layout.addStretch()
        
        # 使用美观的状态指示器替代emoji
        self.status_indicator = StatusIndicator()
        header_layout.addWidget(self.status_indicator)
        status_layout.addLayout(header_layout)
        
        self.status_label = BodyLabel("未登录或登录已过期")
        self.status_label.setStyleSheet("color: #888;")
        status_layout.addWidget(self.status_label)
        
        self.detail_frame = QFrame()
        self.detail_frame.setStyleSheet("background-color: transparent;")
        detail_layout = QVBoxLayout(self.detail_frame)
        detail_layout.setContentsMargins(0, 8, 0, 0)
        detail_layout.setSpacing(6)
        
        self.login_time_label = CaptionLabel()
        self.login_time_label.setStyleSheet("color: #666; background-color: transparent;")
        detail_layout.addWidget(self.login_time_label)
        
        self.expire_time_label = CaptionLabel()
        self.expire_time_label.setStyleSheet("color: #666; background-color: transparent;")
        detail_layout.addWidget(self.expire_time_label)
        
        self.detail_frame.hide()
        status_layout.addWidget(self.detail_frame)
        
        # 按钮区域 - 所有按钮在同一行
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        
        self.login_btn = PrimaryPushButton("扫码登录", icon=FluentIcon.FINGERPRINT)
        self.login_btn.setFixedWidth(120)
        self.login_btn.clicked.connect(self._on_login_clicked)
        btn_layout.addWidget(self.login_btn)
        
        self.refresh_btn = PushButton("刷新状态", icon=FluentIcon.SYNC)
        self.refresh_btn.setFixedWidth(110)
        self.refresh_btn.clicked.connect(self._check_login_status)
        btn_layout.addWidget(self.refresh_btn)
        
        self.clear_btn = PushButton("清除缓存", icon=FluentIcon.DELETE)
        self.clear_btn.setFixedWidth(110)
        self.clear_btn.clicked.connect(self._on_clear_cache)
        btn_layout.addWidget(self.clear_btn)
        
        self.export_btn = PushButton("导出凭证", icon=FluentIcon.SHARE)
        self.export_btn.setFixedWidth(110)
        self.export_btn.setToolTip("将当前登录凭证导出为可分享的字符串")
        self.export_btn.clicked.connect(self._on_export_credential)
        btn_layout.addWidget(self.export_btn)
        
        self.import_btn = PushButton("导入凭证", icon=FluentIcon.DOWNLOAD)
        self.import_btn.setFixedWidth(110)
        self.import_btn.setToolTip("从分享的字符串导入登录凭证")
        self.import_btn.clicked.connect(self._on_import_credential)
        btn_layout.addWidget(self.import_btn)
        
        btn_layout.addStretch()
        status_layout.addLayout(btn_layout)
        
        content_layout.addWidget(status_card)
        
        # 说明卡片
        info_card = CardWidget()
        info_layout = QVBoxLayout(info_card)
        info_layout.setContentsMargins(24, 20, 24, 20)
        info_layout.setSpacing(10)
        
        info_title = SubtitleLabel("登录说明")
        info_layout.addWidget(info_title)
        
        tips = [
            "• 点击「扫码登录」将在当前页面内打开微信公众平台",
            "• 使用微信扫码登录，登录成功后自动保存",
            "• 登录信息有效期约为4天，过期后需重新登录",
            "• 点击「导出凭证」可生成分享字符串，便于在其他设备使用",
            "• 点击「导入凭证」可粘贴他人分享的凭证快速登录",
        ]
        for tip in tips:
            tip_label = BodyLabel(tip)
            tip_label.setStyleSheet("color: #888; padding-left: 8px;")
            info_layout.addWidget(tip_label)
        
        content_layout.addWidget(info_card)
        content_layout.addStretch()
        
        # 设置布局
        status_widget_layout = QVBoxLayout(status_widget)
        status_widget_layout.setContentsMargins(0, 0, 0, 0)
        status_widget_layout.addWidget(page)
        
        return status_widget
    
    def _create_browser_view(self):
        """创建浏览器视图"""
        browser_widget = QWidget()
        # 设置背景色，与应用主题保持一致
        browser_widget.setStyleSheet("background-color: #1a1a1a;")
        layout = QVBoxLayout(browser_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 顶部工具栏
        toolbar = QWidget()
        toolbar.setFixedHeight(50)
        toolbar.setStyleSheet("background-color: #2d2d2d; border-bottom: 1px solid #404040;")
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(16, 8, 16, 8)
        
        self.browser_title = SubtitleLabel("正在加载微信公众平台...")
        self.browser_title.setStyleSheet("color: white;")
        toolbar_layout.addWidget(self.browser_title)
        
        toolbar_layout.addStretch()
        
        self.loading_ring = ProgressRing()
        self.loading_ring.setFixedSize(24, 24)
        self.loading_ring.setStrokeWidth(3)
        toolbar_layout.addWidget(self.loading_ring)
        
        self.cancel_btn = PushButton("取消登录")
        self.cancel_btn.setFixedWidth(100)
        self.cancel_btn.clicked.connect(self._on_cancel_login)
        toolbar_layout.addWidget(self.cancel_btn)
        
        layout.addWidget(toolbar)
        
        # 内嵌浏览器 - 使用自定义页面来拦截新窗口请求
        self.webview = QWebEngineView(self)
        
        # 创建自定义页面并设置到webview
        self.custom_page = CustomWebEnginePage(self.webview)
        self.webview.setPage(self.custom_page)
        
        # 连接信号
        self.webview.urlChanged.connect(self._on_url_changed)
        self.webview.loadStarted.connect(lambda: self.loading_ring.show())
        self.webview.loadFinished.connect(lambda: self.loading_ring.hide())
        layout.addWidget(self.webview)
        
        return browser_widget
    
    def _check_login_status(self):
        """检查登录状态"""
        status = self.login_manager.check_login_status()
        
        if status['isLoggedIn']:
            self.status_indicator.setActive(True)
            self.status_label.setText(status['message'])
            self.status_label.setStyleSheet(f"color: {COLORS['success']};")
            self.login_btn.setText("已登录")
            self.login_btn.setEnabled(False)
            
            self.detail_frame.show()
            self.login_time_label.setText(f"登录时间: {status.get('loginTime', '未知')}")
            self.expire_time_label.setText(f"过期时间: {status.get('expireTime', '未知')}")
            
            self.login_status_changed.emit(True)
        else:
            self.status_indicator.setActive(False)
            self.status_label.setText(status['message'])
            self.status_label.setStyleSheet("color: #888;")
            self.login_btn.setText("扫码登录")
            self.login_btn.setEnabled(True)
            self.detail_frame.hide()
            self.login_status_changed.emit(False)
    
    def _on_login_clicked(self):
        """点击登录 - 在当前页面内显示浏览器"""
        self._start_browser_login()
    
    def _start_browser_login(self):
        """开始浏览器登录流程"""
        self.cookie_collector.clear()
        
        # 清除浏览器cookies
        profile = QWebEngineProfile.defaultProfile()
        profile.cookieStore().deleteAllCookies()
        
        # 切换到浏览器视图
        self.stacked_widget.setCurrentWidget(self.browser_view)
        
        # 加载微信公众平台
        self.browser_title.setText("正在加载微信公众平台...")
        self.webview.load(QUrl("https://mp.weixin.qq.com/"))
    
    def _on_cancel_login(self):
        """取消登录 - 返回状态视图"""
        self.webview.stop()
        self.stacked_widget.setCurrentWidget(self.status_view)
    
    def _on_url_changed(self, url):
        """监听URL变化"""
        url_str = url.toString()
        self.browser_title.setText(f"微信公众平台 - {url.host()}")
        
        # 检测登录成功（URL中包含token）
        token_match = re.search(r'token=(\d+)', url_str)
        if token_match:
            token = token_match.group(1)
            self.browser_title.setText("登录成功，正在保存登录信息...")
            QTimer.singleShot(1500, lambda: self._on_login_success(token))
    
    def _on_login_success(self, token):
        """登录成功处理"""
        cookies = self.cookie_collector.cookies.copy()
        if cookies:
            self.login_manager.token = token
            self.login_manager.cookies = cookies
            self.login_manager.save_cache()
            
            # 切换回状态视图
            self.stacked_widget.setCurrentWidget(self.status_view)
            
            # 更新状态
            self._check_login_status()
            
            # 播放登录成功音效
            play_sound('login')
            
            InfoBar.success(
                title="登录成功",
                content="微信公众平台登录成功！",
                parent=self,
                position=InfoBarPosition.TOP,
                duration=3000
            )
    
    def _on_clear_cache(self):
        """清除缓存"""
        self.login_manager.clear_cache()
        self._check_login_status()
        InfoBar.info(
            title="已清除",
            content="登录缓存已清除",
            parent=self,
            position=InfoBarPosition.TOP,
            duration=2000
        )
    
    def _on_export_credential(self):
        """
        导出登录凭证
        
        将当前的登录信息编码为可分享的字符串，
        并复制到剪贴板，同时显示在对话框中供用户查看。
        """
        # 检查是否已登录
        if not self.login_manager.is_logged_in():
            InfoBar.warning(
                title="无法导出",
                content="当前未登录，请先扫码登录后再导出凭证",
                parent=self,
                position=InfoBarPosition.TOP,
                duration=3000
            )
            return
        
        try:
            # 编码缓存文件
            encoded_str = encode_cache_file(self.login_manager.cache_file)
            
            # 复制到剪贴板
            clipboard = QApplication.clipboard()
            clipboard.setText(encoded_str)
            
            # 显示成功提示和导出结果
            self._show_export_dialog(encoded_str)
            
        except FileNotFoundError:
            InfoBar.error(
                title="导出失败",
                content="缓存文件不存在，请先登录",
                parent=self,
                position=InfoBarPosition.TOP,
                duration=3000
            )
        except Exception as e:
            InfoBar.error(
                title="导出失败",
                content=f"编码过程出错：{str(e)}",
                parent=self,
                position=InfoBarPosition.TOP,
                duration=3000
            )
    
    def _show_export_dialog(self, encoded_str: str):
        """
        显示导出结果对话框
        
        Args:
            encoded_str: 编码后的凭证字符串
        """
        # 播放导出凭证音效
        play_sound('export')
        
        # 创建对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("导出成功")
        dialog.setMinimumSize(500, 300)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #2d2d2d;
                color: white;
            }
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # 成功提示
        success_label = SubtitleLabel("✓ 凭证已导出并复制到剪贴板")
        success_label.setStyleSheet("color: #07C160; font-size: 14px; background-color: transparent;")
        layout.addWidget(success_label)
        
        # 说明
        desc = BodyLabel(f"字符串长度: {len(encoded_str)} 字符")
        desc.setStyleSheet("color: #aaa; background-color: transparent;")
        layout.addWidget(desc)
        
        # 显示编码字符串
        text_edit = PlainTextEdit()
        text_edit.setPlainText(encoded_str)
        text_edit.setReadOnly(True)
        text_edit.setMinimumHeight(100)
        text_edit.setStyleSheet("""
            PlainTextEdit {
                background-color: #1a1a1a;
                border: 1px solid #404040;
                border-radius: 6px;
                color: #07C160;
                padding: 8px;
                font-family: Consolas, Monaco, monospace;
                font-size: 11px;
            }
        """)
        layout.addWidget(text_edit)
        
        # 提示
        tips = CaptionLabel("提示：将此字符串分享给他人，对方可通过「导入凭证」功能使用您的登录状态")
        tips.setStyleSheet("color: #888; background-color: transparent;")
        tips.setWordWrap(True)
        layout.addWidget(tips)
        
        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        copy_btn = PushButton("再次复制", icon=FluentIcon.COPY)
        copy_btn.clicked.connect(lambda: self._copy_to_clipboard(encoded_str))
        btn_layout.addWidget(copy_btn)
        
        close_btn = PrimaryPushButton("关闭")
        close_btn.clicked.connect(dialog.accept)
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)
        
        # 显示成功通知
        InfoBar.success(
            title="导出成功",
            content="凭证已复制到剪贴板，可直接粘贴分享",
            parent=self,
            position=InfoBarPosition.TOP,
            duration=3000
        )
        
        dialog.exec()
    
    def _copy_to_clipboard(self, text: str):
        """复制文本到剪贴板"""
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        InfoBar.success(
            title="已复制",
            content="凭证字符串已复制到剪贴板",
            parent=self,
            position=InfoBarPosition.TOP,
            duration=2000
        )
    
    def _on_import_credential(self):
        """
        导入登录凭证
        
        打开导入对话框，让用户粘贴分享的凭证字符串进行导入。
        """
        dialog = ImportCredentialDialog(self)
        dialog.import_success.connect(self._on_import_success)
        dialog.exec()
    
    def _on_import_success(self):
        """导入成功后的处理"""
        # 重新加载登录管理器的缓存
        self.login_manager.load_cache()
        
        # 刷新登录状态显示
        self._check_login_status()
        
        # 播放登录成功音效（导入凭证相当于登录成功）
        play_sound('login')
        
        # 显示成功提示
        InfoBar.success(
            title="导入成功",
            content="登录凭证已导入，现在可以使用所有功能",
            parent=self,
            position=InfoBarPosition.TOP,
            duration=3000
        )
    
    def is_logged_in(self):
        return self.login_manager.is_logged_in()
    
    def get_login_manager(self):
        return self.login_manager
