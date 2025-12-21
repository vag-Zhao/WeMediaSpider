#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
主窗口模块 - Fluent Design 风格

本模块实现了应用程序的主窗口，基于 qfluentwidgets 的 FluentWindow 构建。
采用侧边导航栏加内容区域的经典布局，支持多页面切换。

主要功能:
    - 自适应屏幕分辨率的窗口大小设置
    - 侧边导航栏管理（支持折叠和展开）
    - 多页面路由和切换
    - 未保存数据的退出确认
    - 页面间信号通信

屏幕适配策略:
    - 小屏幕 (宽度小于1600px): 最小 1100x700，默认 85% 屏幕宽度
    - 中等屏幕 (1600-1920px): 最小 1200x750，默认 80% 屏幕宽度
    - 大屏幕 (大于1920px): 最小 1400x870，默认 75% 屏幕宽度

类说明:
    - ClickOutsideMessageBox: 支持点击遮罩层关闭的消息框
    - MainWindow: 主窗口类，管理所有页面和导航
"""

from PyQt6.QtWidgets import QApplication, QHBoxLayout, QWidget, QFileDialog
from PyQt6.QtCore import Qt, QSize, QTimer
from PyQt6.QtGui import QIcon, QCloseEvent, QScreen

from qfluentwidgets import (
    FluentWindow, NavigationItemPosition, FluentIcon,
    setTheme, Theme, SplashScreen, MessageBox
)
from PyQt6.QtGui import QMouseEvent

from .pages import WelcomePage, LoginPage, UnifiedScrapePage, ResultsPage, SettingsPage, ArticleImagePage, ContentSearchPage
from .app import apply_label_transparent_background


class ClickOutsideMessageBox(MessageBox):
    """支持点击遮罩层关闭的消息框
    
    继承自 qfluentwidgets 的 MessageBox，增加了点击对话框外部区域
    （即遮罩层）时自动关闭的功能。这提供了更好的用户体验，用户可以
    通过点击空白区域来取消操作。
    
    Attributes:
        _clicked_outside: 标记是否通过点击外部关闭
    """
    
    def __init__(self, title: str, content: str, parent=None):
        """初始化消息框
        
        Args:
            title: 对话框标题
            content: 对话框内容文本
            parent: 父窗口，用于模态显示和居中定位
        """
        super().__init__(title, content, parent)
        self._clicked_outside = False
    
    def mousePressEvent(self, event: QMouseEvent):
        """处理鼠标按下事件，检测是否点击在对话框外部"""
        # 获取内部对话框widget的几何区域
        if hasattr(self, 'widget') and self.widget:
            widget_rect = self.widget.geometry()
            if not widget_rect.contains(event.pos()):
                # 点击在对话框外部，标记并关闭
                self._clicked_outside = True
                self.reject()
                return
        super().mousePressEvent(event)
    
    def was_clicked_outside(self) -> bool:
        """检查对话框是否通过点击外部区域关闭
        
        Returns:
            True 表示用户点击了对话框外部区域关闭，
            False 表示用户点击了按钮或按 ESC 关闭
        """
        return self._clicked_outside


class MainWindow(FluentWindow):
    """主窗口类 - 基于 Fluent Design 的导航式布局
    
    继承自 qfluentwidgets 的 FluentWindow，实现了完整的应用程序主界面。
    包含侧边导航栏和多个功能页面，支持页面间的信号通信和数据传递。
    
    页面列表:
        - welcome_page: 欢迎页面，显示应用介绍和快速入口
        - login_page: 登录页面，管理微信登录状态
        - scrape_page: 爬取页面，配置和执行公众号爬取任务
        - article_image_page: 图片提取页面，从文章中提取图片
        - results_page: 结果页面，查看和导出爬取结果
        - content_search_page: 内容搜索页面，搜索文章内容
        - settings_page: 设置页面，配置应用参数
    
    Attributes:
        _screen_width: 屏幕宽度
        _screen_height: 屏幕高度
        _is_small_screen: 是否为小屏幕（宽度小于1600px）
    """
    
    def __init__(self):
        """初始化主窗口，执行窗口设置、页面创建和信号连接"""
        super().__init__()
        
        # 窗口设置
        self.setWindowTitle("微信公众号爬虫")
        
        # 强制设置暗黑主题背景
        self._apply_dark_theme()
        
        # 根据屏幕分辨率自适应窗口大小
        self._setup_window_size()
        
        # 设置侧边栏宽度（根据屏幕大小调整）
        self._setup_navigation()
        
        # 创建页面
        self._create_pages()
        
        # 初始化导航
        self._init_navigation()
        
        # 连接信号
        self._connect_signals()
    
    def _apply_dark_theme(self):
        """强制应用暗黑主题到所有内部组件
        
        FluentWindow 的某些内部组件可能不会自动继承暗黑主题，
        需要手动设置样式表来确保一致的暗黑背景。
        """
        dark_bg = "#1a1a1a"
        
        # 设置主窗口背景
        self.setStyleSheet(f"""
            FluentWindow {{
                background-color: {dark_bg};
            }}
        """)
        
        # 设置 stackedWidget 背景（FluentWindow 的核心内容区域）
        if hasattr(self, 'stackedWidget'):
            self.stackedWidget.setStyleSheet(f"""
                QStackedWidget {{
                    background-color: {dark_bg};
                    border: none;
                }}
                QStackedWidget > QWidget {{
                    background-color: {dark_bg};
                }}
            """)
    
    def _setup_window_size(self):
        """根据屏幕分辨率自适应设置窗口大小
        
        根据主屏幕的可用区域大小，动态计算合适的窗口尺寸。
        采用三档适配策略，确保在不同分辨率下都有良好的显示效果。
        窗口会自动居中显示在屏幕上。
        """
        screen = QApplication.primaryScreen()
        if screen:
            screen_size = screen.availableGeometry()
            screen_width = screen_size.width()
            screen_height = screen_size.height()
            
            # 根据屏幕大小计算合适的窗口尺寸
            # 小屏幕（宽度<1600）：使用较小的最小尺寸
            # 中等屏幕（1600-1920）：使用标准尺寸
            # 大屏幕（>1920）：使用较大尺寸
            
            if screen_width < 1600:
                # 小屏幕适配
                min_width = min(1100, int(screen_width * 0.9))
                min_height = min(700, int(screen_height * 0.85))
                default_width = min(1200, int(screen_width * 0.85))
                default_height = min(750, int(screen_height * 0.85))
            elif screen_width < 1920:
                # 中等屏幕
                min_width = 1200
                min_height = 750
                default_width = min(1400, int(screen_width * 0.8))
                default_height = min(870, int(screen_height * 0.85))
            else:
                # 大屏幕
                min_width = 1400
                min_height = 870
                default_width = min(1600, int(screen_width * 0.75))
                default_height = min(950, int(screen_height * 0.85))
            
            self.setMinimumSize(min_width, min_height)
            self.resize(default_width, default_height)
            
            # 将窗口居中显示
            x = (screen_width - default_width) // 2 + screen_size.x()
            y = (screen_height - default_height) // 2 + screen_size.y()
            self.move(x, y)
            
            # 保存屏幕信息供其他组件使用
            self._screen_width = screen_width
            self._screen_height = screen_height
            self._is_small_screen = screen_width < 1600
        else:
            # 无法获取屏幕信息时使用默认值
            self.setMinimumSize(1100, 700)
            self.resize(1400, 870)
            self._screen_width = 1920
            self._screen_height = 1080
            self._is_small_screen = False
            # 尝试居中（使用备用方法）
            self._center_window_fallback()
    
    def _center_window_fallback(self):
        """备用的窗口居中方法
        
        当主要的居中逻辑无法获取屏幕信息时使用此方法。
        """
        screen = QApplication.primaryScreen()
        if screen:
            screen_geometry = screen.availableGeometry()
            window_geometry = self.frameGeometry()
            center_point = screen_geometry.center()
            window_geometry.moveCenter(center_point)
            self.move(window_geometry.topLeft())
    
    def _setup_navigation(self):
        """配置侧边导航栏
        
        根据屏幕大小调整导航栏的展开宽度，小屏幕使用较窄的宽度。
        导航栏默认展开显示，但允许用户手动折叠。
        """
        # 根据屏幕大小调整侧边栏宽度
        if hasattr(self, '_is_small_screen') and self._is_small_screen:
            self.navigationInterface.setExpandWidth(120)
            self.navigationInterface.setMinimumExpandWidth(120)
        else:
            self.navigationInterface.setExpandWidth(170)
            self.navigationInterface.setMinimumExpandWidth(170)
        
        # 默认展开侧边栏
        self.navigationInterface.setCollapsible(True)  # 允许折叠
        self.navigationInterface.expand(useAni=False)  # 默认展开，不使用动画
    
    def _create_pages(self):
        """创建所有功能页面
        
        实例化各个功能页面并保存为实例属性。
        爬取页面需要传入登录管理器以获取登录凭证。
        创建完成后会延迟应用标签透明背景。
        """
        self.welcome_page = WelcomePage(self)
        self.login_page = LoginPage(self)
        self.results_page = ResultsPage(self)
        self.scrape_page = UnifiedScrapePage(
            self.login_page.get_login_manager(), self
        )
        self.article_image_page = ArticleImagePage(self)
        self.content_search_page = ContentSearchPage(self)
        self.settings_page = SettingsPage(self)
        
        # 延迟应用标签透明背景，确保所有组件都已创建
        QTimer.singleShot(100, self._apply_label_transparency)
    
    def _apply_label_transparency(self):
        """为所有页面的标签组件应用透明背景
        
        遍历所有页面，处理 qfluentwidgets 标签组件的背景透明问题。
        """
        pages = [
            self.welcome_page,
            self.login_page,
            self.results_page,
            self.scrape_page,
            self.article_image_page,
            self.content_search_page,
            self.settings_page
        ]
        for page in pages:
            apply_label_transparent_background(page)
    
    def _connect_signals(self):
        """连接页面间的信号
        
        建立页面之间的通信机制，实现爬取完成跳转、数据放弃返回、
        图片提取请求和设置同步等功能。
        """
        # 爬取完成信号
        self.scrape_page.scrape_completed.connect(self._on_scrape_completed)
        # 数据放弃信号
        self.results_page.data_discarded.connect(self._on_data_discarded)
        # 图片提取请求信号
        self.results_page.extract_images_requested.connect(self._on_extract_images_requested)
        # 设置变更信号 - 同步到爬取页面
        self.settings_page.settings_changed.connect(self._on_settings_changed)
    
    def _on_settings_changed(self, config: dict):
        """处理设置变更事件，将新配置同步到爬取页面"""
        self.scrape_page.apply_settings(config)
    
    def _on_scrape_completed(self, articles: list, source_info: str, temp_file_path: str):
        """处理爬取完成事件，加载结果数据并切换到结果页面"""
        self.results_page.load_articles_data(articles, source_info, temp_file_path)
        self.switchTo(self.results_page)
    
    def _on_data_discarded(self):
        """处理数据放弃事件，返回到爬取页面"""
        self.switchTo(self.scrape_page)
    
    def _on_extract_images_requested(self, url: str):
        """处理图片提取请求，跳转到图片提取页面并填充链接"""
        self.article_image_page.set_article_url(url)
        self.switchTo(self.article_image_page)
    
    def _init_navigation(self):
        """初始化侧边导航项
        
        将所有页面添加到导航栏，设置图标和显示名称。
        设置页面放置在底部位置。
        """
        self.addSubInterface(
            self.welcome_page, FluentIcon.HOME, "欢迎"
        )
        
        self.addSubInterface(
            self.login_page, FluentIcon.FINGERPRINT, "账号登录"
        )
        
        self.addSubInterface(
            self.scrape_page, FluentIcon.DOWNLOAD, "公众号爬取"
        )
        self.addSubInterface(
            self.article_image_page, FluentIcon.PHOTO, "图片提取"
        )
        self.addSubInterface(
            self.results_page, FluentIcon.PIE_SINGLE, "结果查看"
        )
        self.addSubInterface(
            self.content_search_page, FluentIcon.SEARCH, "内容搜索"
        )
        
        self.addSubInterface(
            self.settings_page, FluentIcon.SETTING, "设置",
            NavigationItemPosition.BOTTOM
        )
    
    def closeEvent(self, event: QCloseEvent):
        """处理窗口关闭事件
        
        检查是否有未保存的爬取结果，如果有则显示确认对话框，
        让用户选择保存、放弃或取消关闭操作。
        
        Args:
            event: 关闭事件对象，可通过 accept/ignore 控制是否关闭
        """
        if self.results_page.has_unsaved_data():
            # 有未保存的数据，显示确认对话框（支持点击外部关闭）
            msg_box = ClickOutsideMessageBox(
                "未保存的数据",
                f"您有 {len(self.results_page.articles)} 条爬取结果尚未保存。\n\n请选择操作：",
                self
            )
            
            # 设置按钮文字和宽度
            msg_box.yesButton.setText("保存")
            msg_box.yesButton.setFixedWidth(110)
            msg_box.cancelButton.setText("放弃")
            msg_box.cancelButton.setFixedWidth(110)
            
            # 设置按钮布局间距
            msg_box.buttonLayout.setSpacing(16)
            
            # 使用变量跟踪用户选择
            user_choice = {'action': None}  # 'save', 'discard', 'stay'
            
            def on_save():
                user_choice['action'] = 'save'
            
            def on_discard():
                user_choice['action'] = 'discard'
            
            msg_box.yesButton.clicked.connect(on_save)
            msg_box.cancelButton.clicked.connect(on_discard)
            
            # 点击模态框外部关闭时，action 保持为 None，表示返回（不退出）
            msg_box.exec()
            
            if user_choice['action'] == 'save':
                # 用户选择保存
                self._save_and_exit(event)
            elif user_choice['action'] == 'discard':
                # 用户选择放弃并退出 - 删除临时文件
                self.results_page._delete_temp_file()
                self.results_page._clear_unsaved_data()
                event.accept()
            else:
                # 用户选择返回（不退出）或关闭对话框
                event.ignore()
        else:
            # 没有未保存数据，直接退出
            event.accept()
    
    def _save_and_exit(self, event: QCloseEvent):
        """保存数据并退出
        
        弹出文件保存对话框，让用户选择保存位置。
        保存成功后关闭窗口，保存失败或取消则不退出。
        
        Args:
            event: 关闭事件对象
        """
        import os
        from datetime import datetime
        import csv
        
        # 生成默认文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"results/爬取结果_{timestamp}.csv"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存结果", default_name, "CSV文件 (*.csv)"
        )
        
        if file_path:
            try:
                # 确保目录存在
                os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
                
                articles = self.results_page.articles
                with open(file_path, 'w', encoding='utf-8-sig', newline='') as f:
                    if articles:
                        writer = csv.DictWriter(f, fieldnames=articles[0].keys())
                        writer.writeheader()
                        writer.writerows(articles)
                
                # 保存成功，退出
                self.results_page.is_unsaved = False
                event.accept()
            except Exception as e:
                # 保存失败，显示错误并取消退出
                from qfluentwidgets import InfoBar, InfoBarPosition
                InfoBar.error(
                    title="保存失败",
                    content=str(e),
                    parent=self,
                    position=InfoBarPosition.TOP,
                    duration=3000
                )
                event.ignore()
        else:
            # 用户取消保存，不退出
            event.ignore()
