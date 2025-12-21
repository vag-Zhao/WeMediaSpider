#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文章图片提取页面模块

从微信公众号文章链接中提取所有图片，支持批量下载和 Markdown 文档生成。

主要功能：
    - 解析微信公众号文章页面
    - 提取文章中的所有图片链接
    - 支持图片类型文章和普通图文文章
    - 自动过滤缩略图和重复图片
    - 下载图片到本地（按序号命名）
    - 生成 Markdown 文档（包含图片引用）

技术特点：
    - 支持懒加载图片的 data-src 属性提取
    - 智能识别图片类型文章的特殊结构
    - 从 JavaScript 变量中提取图片列表
    - URL 标准化去重（处理协议和参数差异）
    - 多线程下载避免界面阻塞

使用场景：
    - 保存公众号文章中的图片素材
    - 备份图片类型文章的原图
    - 提取文章配图用于其他用途
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFileDialog,
    QGridLayout, QScrollArea, QLabel
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QPixmap
from datetime import datetime
import os
import re
import json
import requests
import bs4

from qfluentwidgets import (
    TitleLabel, BodyLabel, CaptionLabel, CardWidget,
    PrimaryPushButton, PushButton, LineEdit, TextEdit,
    CheckBox, InfoBar, InfoBarPosition, FluentIcon,
    ProgressBar, ProgressRing
)

from ..styles import COLORS
from ..widgets import CardWidget as CustomCard
from ..utils import play_sound

# 尝试导入爬虫工具函数，用于预处理懒加载图片
try:
    from spider.wechat.utils import _preprocess_lazy_images
except ImportError:
    _preprocess_lazy_images = None


class ImageExtractWorker(QThread):
    """
    图片提取工作线程
    
    在后台线程中执行图片提取和下载任务，避免阻塞主界面。
    
    工作流程：
        1. 获取文章页面 HTML
        2. 解析页面提取标题
        3. 提取所有图片链接（去重）
        4. 生成 Markdown 文档
        5. 下载图片到本地（可选）
    
    Signals:
        progress_update: 进度更新 (current, total, message)
        image_found: 发现图片 (index, url, alt)
        extract_success: 提取成功 (title, images, md_content)
        extract_failed: 提取失败 (error_message)
        download_progress: 下载进度 (current, total, message)
        download_complete: 下载完成 (folder_path)
    """
    
    # 信号定义
    progress_update = pyqtSignal(int, int, str)
    image_found = pyqtSignal(int, str, str)
    extract_success = pyqtSignal(str, list, str)
    extract_failed = pyqtSignal(str)
    download_progress = pyqtSignal(int, int, str)
    download_complete = pyqtSignal(str)
    
    def __init__(self, url: str, output_dir: str, save_images: bool = True, parent=None):
        """
        初始化工作线程
        
        Args:
            url: 文章链接
            output_dir: 输出目录
            save_images: 是否下载图片到本地
            parent: 父对象
        """
        super().__init__(parent)
        self.url = url
        self.output_dir = output_dir
        self.save_images = save_images
        self._is_cancelled = False
        
        # HTTP 请求头，模拟浏览器访问
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }
    
    def cancel(self):
        """
        取消任务
        
        设置取消标志，线程会在下一个检查点停止执行。
        """
        self._is_cancelled = True
    
    def run(self):
        """
        执行图片提取任务
        
        这是线程的主入口，按顺序执行：
        获取页面 -> 解析内容 -> 提取图片 -> 生成文档 -> 下载图片
        """
        try:
            self.progress_update.emit(0, 100, "正在获取文章页面...")
            
            # 获取页面内容
            response = requests.get(self.url, headers=self.headers, timeout=30)
            if response.status_code != 200:
                self.extract_failed.emit(f"请求失败，状态码: {response.status_code}")
                return
            
            if self._is_cancelled:
                return
            
            self.progress_update.emit(20, 100, "正在解析页面内容...")
            
            # 解析HTML
            soup = bs4.BeautifulSoup(response.text, 'lxml')
            
            # 提取标题
            title = self._extract_title(soup)
            if not title:
                title = f"文章_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # 清理标题中的非法字符
            safe_title = self._sanitize_filename(title)
            
            if self._is_cancelled:
                return
            
            self.progress_update.emit(40, 100, "正在提取图片链接...")
            
            # 提取图片
            images = self._extract_images(soup)
            
            if not images:
                self.extract_failed.emit("未找到任何图片")
                return
            
            # 发送每张图片的信息
            for i, (url, alt) in enumerate(images):
                self.image_found.emit(i + 1, url, alt)
            
            if self._is_cancelled:
                return
            
            self.progress_update.emit(60, 100, "正在生成Markdown文档...")
            
            # 生成Markdown内容
            md_content = self._generate_markdown(title, images)
            
            # 创建输出目录
            output_folder = os.path.join(self.output_dir, safe_title)
            os.makedirs(output_folder, exist_ok=True)
            
            # 保存Markdown文件
            md_file = os.path.join(output_folder, f"{safe_title}.md")
            with open(md_file, 'w', encoding='utf-8') as f:
                f.write(md_content)
            
            if self._is_cancelled:
                return
            
            # 下载图片
            if self.save_images:
                self.progress_update.emit(70, 100, "正在下载图片...")
                self._download_images(images, output_folder)
            
            if self._is_cancelled:
                return
            
            self.progress_update.emit(100, 100, "完成！")
            self.extract_success.emit(title, images, md_content)
            self.download_complete.emit(output_folder)
            
        except Exception as e:
            self.extract_failed.emit(f"提取失败: {str(e)}")
    
    def _extract_title(self, soup) -> str:
        """
        提取文章标题
        
        按优先级尝试多个选择器，返回第一个有效的标题。
        
        Args:
            soup: BeautifulSoup 解析对象
            
        Returns:
            str: 文章标题，未找到时返回空字符串
        """
        # 按优先级尝试多个选择器
        title_selectors = [
            '#activity-name',
            '.rich_media_title',
            'h1',
            'title'
        ]
        
        for selector in title_selectors:
            ele = soup.select_one(selector)
            if ele:
                title = ele.get_text(strip=True)
                if title:
                    return title
        
        return ""
    
    def _extract_images(self, soup) -> list:
        """
        提取所有图片链接
        
        使用统一的去重逻辑，支持多种文章类型。
        
        核心策略：
            1. 使用全局 seen_urls 集合进行严格去重
            2. URL 标准化：统一协议、移除查询参数、解码 HTML 实体
            3. 优先使用 JS 方法提取（最可靠），成功后直接返回
            4. 只有 JS 方法失败时才使用其他方法
        
        提取顺序：
            方法0: .swiper_item_img 容器（图片类型文章）
            方法1: .swiper_item[data-src]（图片类型文章备用）
            方法2: JavaScript 变量提取
            方法3: 内容区域 img 标签（普通图文文章）
            方法4: 全文档 img 标签（最后手段）
        
        Args:
            soup: BeautifulSoup 解析对象
            
        Returns:
            list: 图片列表 [(url, alt), ...]
        """
        import html
        
        images = []
        seen_urls = set()  # 全局去重集合
        
        def decode_html_entities(text):
            """解码HTML实体和转义字符"""
            if not text:
                return text
            # 解码HTML实体
            text = html.unescape(text)
            # 处理双重转义
            def replace_hex_escape(match):
                hex_val = match.group(1)
                try:
                    return chr(int(hex_val, 16))
                except:
                    return match.group(0)
            text = re.sub(r'\\x([0-9a-fA-F]{2})', replace_hex_escape, text)
            text = html.unescape(text)
            return text
        
        def normalize_url(url):
            """标准化URL用于去重 - 这是去重的核心函数
            
            处理以下情况：
            1. http vs https 协议差异 -> 统一为https
            2. URL查询参数差异 -> 移除所有查询参数
            3. HTML实体编码差异 -> 解码所有实体
            4. 尾部斜杠差异 -> 移除尾部斜杠
            """
            if not url:
                return ''
            # 解码HTML实体
            url = decode_html_entities(url)
            # 统一使用https协议进行比较（关键！）
            url = url.replace('http://', 'https://')
            # 移除查询参数（关键！微信图片URL的查询参数可能不同但图片相同）
            base_url = url.split('?')[0] if '?' in url else url
            # 移除尾部斜杠
            base_url = base_url.rstrip('/')
            return base_url
        
        def is_thumbnail_url(url, strict_mode=False):
            """检查是否是缩略图URL
            
            微信图片URL格式（图片类型文章）：
            - 原图: .../xxx/0?wx_fmt=... (路径以 /0? 结尾)
            - 缩略图: .../xxx/300?wx_fmt=... (路径以 /数字? 结尾，数字表示尺寸)
            
            普通图文文章的图片URL格式：
            - 正常图片: .../xxx/640?wx_fmt=... (这不是缩略图！)
            
            参数：
            - strict_mode: 严格模式，只在图片类型文章中使用
                          普通图文文章不应该使用严格模式
            
            缩略图特征（仅在严格模式下检测）：
            1. URL路径中包含 /数字? 且数字不为0
            2. 通常出现在 background-image 样式中
            """
            if not url:
                return False
            
            # 非严格模式下，不过滤任何URL（普通图文文章）
            if not strict_mode:
                return False
            
            # 严格模式：检查是否是缩略图（路径以 /非零数字? 结尾）
            # 例如 /300? /640? /1080? 等都是缩略图
            import re
            # 匹配 /数字? 格式，数字不为0
            thumbnail_pattern = r'/([1-9]\d*)\?'
            if re.search(thumbnail_pattern, url):
                return True
            return False
        
        # 标记是否是图片类型文章（用于决定是否启用严格缩略图过滤）
        is_picture_article = False
        
        def add_image(src, alt='', strict_thumbnail_filter=False):
            """添加图片到列表（带严格去重）
            
            参数：
            - src: 图片URL
            - alt: 图片描述
            - strict_thumbnail_filter: 是否启用严格缩略图过滤（仅图片类型文章使用）
            
            返回值：True表示成功添加，False表示被过滤或重复
            """
            nonlocal images, seen_urls
            
            if not src:
                return False
            
            # 解码URL中的HTML实体
            src = decode_html_entities(src)
            
            # 验证是否是有效的微信图片URL
            if 'mmbiz.qpic.cn' not in src:
                return False
            if 'pic_blank' in src or 'data:image' in src:
                return False
            
            # 过滤缩略图（仅在严格模式下，用于图片类型文章）
            if is_thumbnail_url(src, strict_mode=strict_thumbnail_filter):
                print(f"[DEBUG] 跳过缩略图: {src[:60]}...")
                return False
            
            # 标准化URL用于去重（核心去重逻辑）
            normalized = normalize_url(src)
            
            # 严格去重检查
            if normalized in seen_urls:
                print(f"[DEBUG] 跳过重复图片: {src[:60]}...")
                return False
            
            # 添加到去重集合
            seen_urls.add(normalized)
            
            # 过滤表情图片（通常alt是表情名称如[加油]）
            if alt and alt.startswith('[') and alt.endswith(']') and len(alt) < 10:
                return False
            
            if not alt:
                alt = f'图片{len(images) + 1}'
            
            images.append((src, alt))
            print(f"[DEBUG] 添加图片 {len(images)}: {src[:60]}...")
            return True
        
        # 预处理懒加载图片（复用爬虫的逻辑）
        if _preprocess_lazy_images:
            _preprocess_lazy_images(soup)
        else:
            # 如果无法导入，手动处理
            for img in soup.find_all('img'):
                src = img.get('src', '')
                data_src = img.get('data-src', '')
                if data_src and (not src or 'data:image/svg' in src or 'pic_blank' in src):
                    img['src'] = data_src
        
        # 需要排除的图片类名（头像等非内容图片）
        excluded_classes = [
            'wx_follow_avatar_pic',
            'jump_author_avatar',
            'avatar',
            'profile_avatar',
            'icon'
        ]
        
        def is_excluded_image(img):
            """检查是否是需要排除的图片"""
            img_class = img.get('class', [])
            if isinstance(img_class, str):
                img_class = img_class.split()
            
            for cls in img_class:
                for excluded in excluded_classes:
                    if excluded in cls.lower():
                        return True
            return False
        
        def is_content_image(src):
            """检查是否是内容图片"""
            if not src:
                return False
            # 解码URL
            src = decode_html_entities(src)
            if 'mmbiz.qpic.cn' not in src:
                return False
            if 'data:image/svg' in src:
                return False
            if 'pic_blank' in src:
                return False
            return True
        
        # ========== 图片类型文章专用提取方法 ==========
        # 微信图片类型文章的HTML结构：
        # - 原图：在 .swiper_item_img 容器内的 <img> 标签中
        # - 缩略图：在 .swiper_indicator_item_pc 的 background-image 样式中（需要排除）
        #
        # 关键区别：
        # - 原图URL格式：/0?wx_fmt=... （路径以 /0? 结尾）
        # - 缩略图URL格式：/300?wx_fmt=... （路径以 /数字? 结尾，数字不为0）
        
        print("[DEBUG] ========== 开始提取图片 ==========")
        
        # 方法0: 严格从 .swiper_item_img 容器内提取（最可靠）
        # 这是图片类型文章的唯一正确来源
        print("[DEBUG] 方法0: 尝试从 .swiper_item_img 容器提取...")
        swiper_containers = soup.select('.swiper_item_img')
        print(f"[DEBUG] 找到 {len(swiper_containers)} 个 .swiper_item_img 容器")
        
        if swiper_containers:
            is_picture_article = True  # 标记为图片类型文章
        
        for container in swiper_containers:
            # 只从容器内的 img 标签提取
            for img in container.find_all('img'):
                src = img.get('src') or img.get('data-src') or ''
                print(f"[DEBUG] 检查图片: {src[:80] if src else 'None'}...")
                if src and 'mmbiz.qpic.cn' in src:
                    alt = img.get('alt') or ''
                    # 图片类型文章使用严格缩略图过滤
                    add_image(src, alt, strict_thumbnail_filter=True)
        
        if images:
            print(f"[DEBUG] 方法0成功！从 .swiper_item_img 提取到 {len(images)} 张图片")
            return images
        
        print("[DEBUG] 方法0未找到图片，尝试方法1...")
        
        # 方法1: 从 swiper_item 容器的 data-src 属性提取
        print("[DEBUG] 方法1: 尝试从 .swiper_item[data-src] 提取...")
        swiper_items = soup.select('.swiper_item[data-src]')
        print(f"[DEBUG] 找到 {len(swiper_items)} 个带 data-src 的 .swiper_item")
        
        if swiper_items:
            is_picture_article = True  # 标记为图片类型文章
        
        for item in swiper_items:
            src = item.get('data-src', '')
            if src and 'mmbiz.qpic.cn' in src:
                # 图片类型文章使用严格缩略图过滤
                add_image(src, strict_thumbnail_filter=True)
        
        if images:
            print(f"[DEBUG] 方法1成功！从 .swiper_item data-src 提取到 {len(images)} 张图片")
            return images
        
        print("[DEBUG] 方法1未找到图片，尝试方法2...")
        
        # 方法2: 从 JavaScript 变量提取（备用）
        print("[DEBUG] 方法2: 尝试从JS变量提取...")
        js_images = self._extract_images_from_js(soup)
        
        if js_images:
            print(f"[DEBUG] 方法2成功！JS方法提取到 {len(js_images)} 张图片")
            return js_images
        
        print("[DEBUG] 方法2未找到图片，尝试方法3...")
        
        # 方法3: 从普通图文文章的内容区域提取（增强版）
        # 普通图文文章的图片特点：
        # 1. 图片在 #js_content 或 .rich_media_content 容器内
        # 2. 真正的图片URL在 data-src 属性中（src 可能是SVG占位符）
        # 3. 需要过滤小图标（data-w 小于某个阈值的是装饰图标）
        # 4. 正文图片宽度通常是 1080
        print("[DEBUG] 方法3: 尝试从内容区域提取（增强版）...")
        
        # 最小图片宽度阈值（过滤小图标）
        MIN_IMAGE_WIDTH = 200
        
        CONTENT_SELECTORS = [
            "#js_content",
            ".rich_media_content",
            "#js_image_content",
            ".image_content",
        ]
        
        for selector in CONTENT_SELECTORS:
            content_ele = soup.select_one(selector)
            if content_ele:
                print(f"[DEBUG] 找到内容区域: {selector}")
                for img in content_ele.find_all('img'):
                    if is_excluded_image(img):
                        continue
                    
                    # 优先使用 data-src（真正的图片URL），其次是 src
                    src = img.get('data-src') or img.get('src') or ''
                    
                    # 跳过SVG占位符
                    if 'data:image/svg' in src:
                        continue
                    
                    if not is_content_image(src):
                        continue
                    
                    # 检查图片宽度，过滤小图标
                    data_w = img.get('data-w', '')
                    if data_w:
                        try:
                            width = int(data_w)
                            if width < MIN_IMAGE_WIDTH:
                                print(f"[DEBUG] 跳过小图标 (宽度={width}): {src[:50]}...")
                                continue
                        except ValueError:
                            pass
                    
                    alt = img.get('alt') or ''
                    add_image(src, alt)
        
        if images:
            print(f"[DEBUG] 方法3成功！从内容区域提取到 {len(images)} 张图片")
            return images
        
        print("[DEBUG] 方法3未找到图片，尝试方法4...")
        
        # 方法4: 从整个文档的 img 标签提取（最后手段）
        # 注意：这个方法可能会提取到不需要的图片，所以放在最后
        print("[DEBUG] 方法4: 尝试从整个文档提取...")
        all_imgs = soup.find_all('img')
        print(f"[DEBUG] 文档中共有 {len(all_imgs)} 个 img 标签")
        
        for img in all_imgs:
            if is_excluded_image(img):
                continue
            
            src = img.get('src') or img.get('data-src') or ''
            
            if not is_content_image(src):
                continue
            
            alt = img.get('alt') or ''
            add_image(src, alt)
        
        print(f"[DEBUG] 最终提取 {len(images)} 张图片")
        return images
    
    def _extract_images_from_js(self, soup) -> list:
        """
        从 JavaScript 变量中提取图片
        
        专门处理微信图片类型文章，从 picture_page_info_list 变量提取。
        
        数据结构说明：
            每个图片对象包含多个 URL 字段：
            - cdn_url: 原图 URL（我们需要的）
            - cdn_url_1: 可能是缩略图或其他版本
            - cdn_url_xxx: 其他版本
        
        去重策略：
            只提取 "cdn_url" 字段（不带后缀数字的），
            避免正则表达式匹配所有 cdn_url 开头的字段导致重复。
        
        Args:
            soup: BeautifulSoup 解析对象
            
        Returns:
            list: 图片列表 [(url, alt), ...]，已去重
        """
        import html
        images = []
        seen_urls = set()  # 独立的去重集合
        
        def decode_html_entities(text):
            """解码HTML实体和转义字符"""
            if not text:
                return text
            # 解码HTML实体（如 &amp; -> &, &lt; -> <）
            text = html.unescape(text)
            # 处理双重转义
            def replace_hex_escape(match):
                hex_val = match.group(1)
                try:
                    return chr(int(hex_val, 16))
                except:
                    return match.group(0)
            text = re.sub(r'\\x([0-9a-fA-F]{2})', replace_hex_escape, text)
            # 再次解码HTML实体
            text = html.unescape(text)
            return text
        
        def normalize_url_for_dedup(url):
            """标准化URL用于去重
            
            关键：提取URL的核心部分用于比较，忽略协议和查询参数差异
            """
            if not url:
                return ''
            url = decode_html_entities(url)
            # 统一使用https协议
            url = url.replace('http://', 'https://')
            # 移除查询参数
            base_url = url.split('?')[0] if '?' in url else url
            # 移除尾部斜杠
            base_url = base_url.rstrip('/')
            return base_url
        
        def is_thumbnail_url_strict(url):
            """检查是否是缩略图URL（严格模式，仅用于图片类型文章）
            
            图片类型文章的URL格式：
            - 原图: /0?wx_fmt=... (路径以 /0? 结尾)
            - 缩略图: /300?wx_fmt=... (路径以 /数字? 结尾，数字不为0)
            """
            if not url:
                return False
            # 匹配 /数字? 格式，数字不为0（缩略图特征）
            thumbnail_pattern = r'/([1-9]\d*)\?'
            if re.search(thumbnail_pattern, url):
                return True
            return False
        
        def add_image(cdn_url):
            """添加图片到列表（带严格去重）"""
            if not cdn_url or 'mmbiz.qpic.cn' not in cdn_url:
                return False
            
            # 解码 URL 中的转义字符和 HTML 实体
            cdn_url = decode_html_entities(cdn_url)
            
            # 过滤缩略图（图片类型文章使用严格模式）
            if is_thumbnail_url_strict(cdn_url):
                print(f"[DEBUG] JS方法跳过缩略图: {cdn_url[:60]}...")
                return False
            
            # 标准化URL用于去重
            normalized = normalize_url_for_dedup(cdn_url)
            
            if normalized in seen_urls:
                print(f"[DEBUG] JS方法跳过重复图片: {normalized[-50:]}...")
                return False
            
            seen_urls.add(normalized)
            
            # 统一使用https协议存储
            final_url = cdn_url.replace('http://', 'https://')
            images.append((final_url, f'图片{len(images) + 1}'))
            print(f"[DEBUG] JS方法添加图片 {len(images)}: {final_url[:60]}...")
            return True
        
        # 查找包含 picture_page_info_list 的 script 标签
        for script in soup.find_all('script'):
            script_text = script.string or ''
            
            # 检查是否包含图片列表变量
            if 'picture_page_info_list' in script_text:
                print(f"[DEBUG] 找到 picture_page_info_list，脚本长度: {len(script_text)}")
                
                # ========== 核心修复：只提取顶层 cdn_url ==========
                #
                # picture_page_info_list 的实际数据结构（JS格式，非JSON）：
                # [
                #   {
                #     width: '1280' * 1,
                #     height: '1809' * 1,
                #     cdn_url: 'https://...',          <-- 我们需要的（顶层）
                #     watermark_info: {
                #       cdn_url: 'http://...'          <-- 不需要（嵌套）
                #     },
                #     share_cover: {
                #       cdn_url: 'https://...'         <-- 不需要（嵌套）
                #     }
                #   },
                #   ...
                # ]
                #
                # 关键特征：
                # 1. 字段名没有引号（width: 而不是 "width":）
                # 2. 值使用单引号（'1280' 而不是 "1280"）
                # 3. 顶层 cdn_url 紧跟在 height 字段后面
                # 4. 嵌套的 cdn_url 在 watermark_info 或 share_cover 对象内部
                #
                # 方法：匹配 height: '数字' * 1, 后面紧跟的 cdn_url
                # ================================================
                
                # 方法1: 精确匹配顶层 cdn_url（紧跟在 height 字段后面）
                # 实际格式: height: '1809' * 1,\n      cdn_url: 'https://...',
                # 注意：字段名没有引号，值使用单引号
                
                # 正则：匹配 height: '数字' * 1, 后面的 cdn_url: 'URL'
                # 这个模式只会匹配顶层的 cdn_url，因为嵌套的 cdn_url 前面没有 height
                top_level_pattern = r"height:\s*'(\d+)'\s*\*\s*1,\s*cdn_url:\s*'([^']+)'"
                
                # 先尝试找到所有匹配
                all_matches = list(re.finditer(top_level_pattern, script_text))
                print(f"[DEBUG] 顶层cdn_url正则匹配到 {len(all_matches)} 个")
                
                # 收集有效URL
                valid_urls = []
                for match in all_matches:
                    # 获取URL（第2组是cdn_url的值）
                    url = match.group(2)
                    if url and 'mmbiz.qpic.cn' in url:
                        # 打印完整URL用于调试
                        print(f"[DEBUG] 匹配到顶层URL: {url[:80]}...")
                        valid_urls.append(url)
                
                print(f"[DEBUG] 顶层有效URL数量: {len(valid_urls)}")
                
                # 添加有效的URL
                for url in valid_urls:
                    add_image(url)
                
                if images:
                    print(f"[DEBUG] 从 picture_page_info_list 提取到 {len(images)} 张图片")
                    return images
                
                # 方法2: 如果方法1失败，尝试JSON解析（只提取顶层 cdn_url）
                print("[DEBUG] 顶层正则方法未找到图片，尝试JSON解析...")
                match = re.search(r'var\s+picture_page_info_list\s*=\s*(\[[\s\S]*?\])\s*;', script_text)
                if not match:
                    match = re.search(r'var\s+picture_page_info_list\s*=\s*(\[.*?\]);', script_text, re.DOTALL)
                
                if match:
                    try:
                        json_str = match.group(1)
                        # 处理 JsDecode 包装
                        json_str = re.sub(r'JsDecode\(["\']([^"\']+)["\']\)', r'"\1"', json_str)
                        # 解码 HTML 实体
                        json_str = decode_html_entities(json_str)
                        # 移除尾部逗号
                        json_str = re.sub(r',\s*([}\]])', r'\1', json_str)
                        
                        pic_list = json.loads(json_str)
                        print(f"[DEBUG] JSON解析成功，共 {len(pic_list)} 个对象")
                        
                        for pic_info in pic_list:
                            # 只获取 cdn_url 字段，不获取 cdn_url_1 等
                            cdn_url = pic_info.get('cdn_url', '')
                            if cdn_url:
                                add_image(cdn_url)
                        
                        if images:
                            print(f"[DEBUG] 从 JSON 解析提取到 {len(images)} 张图片")
                            return images
                    except json.JSONDecodeError as e:
                        print(f"[DEBUG] JSON 解析失败: {e}")
                    except Exception as e:
                        print(f"[DEBUG] JSON 处理异常: {e}")
        
        return images
    
    def _generate_markdown(self, title: str, images: list) -> str:
        """
        生成 Markdown 文档
        
        创建包含文章信息和图片列表的 Markdown 文件。
        
        Args:
            title: 文章标题
            images: 图片列表 [(url, alt), ...]
            
        Returns:
            str: Markdown 文档内容
        """
        lines = [
            f"# {title}",
            "",
            f"> 提取时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"> 图片数量: {len(images)}",
            "",
            "## 图片列表",
            ""
        ]
        
        for i, (url, alt) in enumerate(images, 1):
            # 本地图片引用
            ext = self._get_image_extension(url)
            local_name = f"{i}{ext}"
            lines.append(f"### 图片 {i}")
            lines.append("")
            lines.append(f"![{alt}]({local_name})")
            lines.append("")
            lines.append(f"原始链接: {url}")
            lines.append("")
        
        return '\n'.join(lines)
    
    def _download_images(self, images: list, output_folder: str):
        """
        下载所有图片到本地
        
        按序号命名图片文件（1.jpg, 2.png, ...）。
        
        Args:
            images: 图片列表 [(url, alt), ...]
            output_folder: 输出文件夹路径
        """
        total = len(images)
        
        for i, (url, alt) in enumerate(images):
            if self._is_cancelled:
                return
            
            self.download_progress.emit(i + 1, total, f"下载图片 {i + 1}/{total}")
            
            try:
                # 获取图片扩展名
                ext = self._get_image_extension(url)
                filename = f"{i + 1}{ext}"
                filepath = os.path.join(output_folder, filename)
                
                # 下载图片
                response = requests.get(url, headers=self.headers, timeout=30)
                if response.status_code == 200:
                    with open(filepath, 'wb') as f:
                        f.write(response.content)
            except Exception as e:
                print(f"下载图片失败: {url}, 错误: {e}")
    
    def _get_image_extension(self, url: str) -> str:
        """
        从 URL 获取图片扩展名
        
        优先从 wx_fmt 参数获取，其次从 URL 路径推断。
        
        Args:
            url: 图片 URL
            
        Returns:
            str: 文件扩展名（如 .jpg, .png）
        """
        # 从 URL 参数中获取格式
        if 'wx_fmt=' in url:
            match = re.search(r'wx_fmt=(\w+)', url)
            if match:
                fmt = match.group(1).lower()
                if fmt in ['png', 'jpg', 'jpeg', 'gif', 'webp']:
                    return f'.{fmt}'
        
        # 从URL路径中获取
        if '.png' in url.lower():
            return '.png'
        elif '.jpg' in url.lower() or '.jpeg' in url.lower():
            return '.jpg'
        elif '.gif' in url.lower():
            return '.gif'
        elif '.webp' in url.lower():
            return '.webp'
        
        # 默认jpg
        return '.jpg'
    
    def _sanitize_filename(self, filename: str) -> str:
        """清理文件名中的非法字符"""
        # 移除Windows文件名非法字符
        illegal_chars = r'[\\/:*?"<>|]'
        safe_name = re.sub(illegal_chars, '', filename)
        # 移除首尾空格
        safe_name = safe_name.strip()
        # 限制长度
        if len(safe_name) > 100:
            safe_name = safe_name[:100]
        return safe_name or "untitled"


class ArticleImagePage(QWidget):
    """
    文章图片提取页面
    
    提供从微信公众号文章链接提取图片的完整界面。
    
    界面布局：
        - 左侧：文章链接输入和保存配置
        - 右侧：提取结果预览（标题、数量、链接列表）
        - 底部：进度条和操作按钮
    
    Attributes:
        worker: 图片提取工作线程
        _output_folder: 最近一次提取的输出文件夹
        _image_urls: 提取到的图片 URL 列表
    """
    
    def __init__(self, parent=None):
        """
        初始化图片提取页面
        
        Args:
            parent: 父控件
        """
        super().__init__(parent)
        self.setObjectName("articleImagePage")
        self.worker = None
        self._setup_ui()
        self._apply_dark_background()
    
    def _apply_dark_background(self):
        """应用暗黑背景样式"""
        self.setStyleSheet("background-color: #1a1a1a;")
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(12)
        
        # 标题
        title = TitleLabel("文章图片提取")
        layout.addWidget(title)
        
        # 说明
        desc = CaptionLabel("从微信公众号文章链接提取所有图片，保存为Markdown文档和图片文件")
        desc.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")
        layout.addWidget(desc)
        
        # 主内容区域 - 水平布局
        content_layout = QHBoxLayout()
        content_layout.setSpacing(12)
        
        # 左侧：输入和配置
        self._setup_input_area(content_layout)
        
        # 右侧：结果预览
        self._setup_result_area(content_layout)
        
        layout.addLayout(content_layout, 1)
        
        # 底部：进度和按钮
        self._setup_bottom_area(layout)
    
    def _setup_input_area(self, parent_layout):
        """设置输入区域"""
        input_card = CardWidget()
        input_layout = QVBoxLayout(input_card)
        input_layout.setContentsMargins(16, 12, 16, 12)
        input_layout.setSpacing(10)
        
        # 标题
        input_title = BodyLabel("文章链接")
        input_title.setStyleSheet("font-weight: bold; font-size: 13px; color: #0078d4;")
        input_layout.addWidget(input_title)
        
        # URL输入
        url_hint = CaptionLabel("请输入微信公众号文章链接")
        url_hint.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 11px;")
        input_layout.addWidget(url_hint)
        
        self.url_input = LineEdit()
        self.url_input.setPlaceholderText("https://mp.weixin.qq.com/s/...")
        self.url_input.setClearButtonEnabled(True)
        input_layout.addWidget(self.url_input)
        
        # 配置区域
        config_title = BodyLabel("保存配置")
        config_title.setStyleSheet("font-weight: bold; font-size: 13px; color: #0078d4; margin-top: 10px;")
        input_layout.addWidget(config_title)
        
        # 输出目录
        output_row = QHBoxLayout()
        output_row.setSpacing(8)
        output_label = BodyLabel("输出目录")
        output_label.setFixedWidth(60)
        output_row.addWidget(output_label)
        # 导入默认输出目录
        from gui.utils import DEFAULT_OUTPUT_DIR
        
        self.output_input = LineEdit()
        self.output_input.setText(DEFAULT_OUTPUT_DIR)  # 使用用户文档目录，避免权限问题
        self.output_input.setPlaceholderText("输出目录")
        output_row.addWidget(self.output_input)
        browse_btn = PushButton("浏览", icon=FluentIcon.FOLDER)
        browse_btn.setFixedWidth(70)
        browse_btn.clicked.connect(self._on_browse_output)
        output_row.addWidget(browse_btn)
        input_layout.addLayout(output_row)
        
        # 选项
        self.save_images_check = CheckBox("下载图片到本地（按1,2,3...顺序命名）")
        self.save_images_check.setChecked(True)
        # 强制设置 CheckBox 透明背景
        self.save_images_check.setStyleSheet("""
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
        input_layout.addWidget(self.save_images_check)
        
        self.save_md_check = CheckBox("生成Markdown文档（包含图片链接）")
        self.save_md_check.setChecked(True)
        self.save_md_check.setEnabled(False)  # 始终生成MD
        # 强制设置 CheckBox 透明背景
        self.save_md_check.setStyleSheet("""
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
            CheckBox:disabled, QCheckBox:disabled {
                color: #888888;
            }
        """)
        input_layout.addWidget(self.save_md_check)
        
        input_layout.addStretch()
        parent_layout.addWidget(input_card, 1)
    
    def _setup_result_area(self, parent_layout):
        """设置结果预览区域"""
        result_card = CardWidget()
        result_layout = QVBoxLayout(result_card)
        result_layout.setContentsMargins(16, 12, 16, 12)
        result_layout.setSpacing(8)
        
        # 标题
        result_title = BodyLabel("提取结果")
        result_title.setStyleSheet("font-weight: bold; font-size: 13px; color: #0078d4;")
        result_layout.addWidget(result_title)
        
        # 文章标题显示
        title_row = QHBoxLayout()
        title_label = BodyLabel("文章标题:")
        title_label.setFixedWidth(70)
        title_row.addWidget(title_label)
        self.article_title_label = BodyLabel("等待提取...")
        self.article_title_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        self.article_title_label.setWordWrap(True)
        title_row.addWidget(self.article_title_label, 1)
        result_layout.addLayout(title_row)
        
        # 图片数量
        count_row = QHBoxLayout()
        count_label = BodyLabel("图片数量:")
        count_label.setFixedWidth(70)
        count_row.addWidget(count_label)
        self.image_count_label = BodyLabel("0")
        self.image_count_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        count_row.addWidget(self.image_count_label)
        count_row.addStretch()
        result_layout.addLayout(count_row)
        
        # 图片列表预览
        list_label = BodyLabel("图片链接预览:")
        list_label.setStyleSheet("margin-top: 8px;")
        result_layout.addWidget(list_label)
        
        self.image_list_text = TextEdit()
        self.image_list_text.setReadOnly(True)
        self.image_list_text.setPlaceholderText("提取的图片链接将显示在这里...")
        result_layout.addWidget(self.image_list_text, 1)
        
        parent_layout.addWidget(result_card, 1)
    
    def _setup_bottom_area(self, parent_layout):
        """设置底部区域"""
        # 进度条
        progress_layout = QHBoxLayout()
        self.progress_bar = ProgressBar()
        self.progress_bar.setFixedHeight(4)
        self.progress_bar.hide()
        progress_layout.addWidget(self.progress_bar)
        parent_layout.addLayout(progress_layout)
        
        # 状态标签
        self.status_label = CaptionLabel("")
        self.status_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        parent_layout.addWidget(self.status_label)
        
        # 按钮行
        btn_layout = QHBoxLayout()
        
        self.extract_btn = PrimaryPushButton("开始提取", icon=FluentIcon.DOWNLOAD)
        self.extract_btn.setFixedWidth(140)
        self.extract_btn.clicked.connect(self._on_start_extract)
        btn_layout.addWidget(self.extract_btn)
        
        self.cancel_btn = PushButton("取消", icon=FluentIcon.CLOSE)
        self.cancel_btn.setFixedWidth(100)
        self.cancel_btn.clicked.connect(self._on_cancel)
        self.cancel_btn.hide()
        btn_layout.addWidget(self.cancel_btn)
        
        self.open_folder_btn = PushButton("打开文件夹", icon=FluentIcon.FOLDER)
        self.open_folder_btn.setFixedWidth(120)
        self.open_folder_btn.clicked.connect(self._on_open_folder)
        self.open_folder_btn.hide()
        btn_layout.addWidget(self.open_folder_btn)
        
        btn_layout.addStretch()
        parent_layout.addLayout(btn_layout)
    
    def _on_browse_output(self):
        """选择输出目录"""
        dir_path = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if dir_path:
            self.output_input.setText(dir_path)
    
    def _on_start_extract(self):
        """开始提取"""
        url = self.url_input.text().strip()
        if not url:
            InfoBar.warning(
                title="提示",
                content="请输入文章链接",
                parent=self,
                position=InfoBarPosition.TOP,
                duration=2000
            )
            return
        
        # 验证URL格式
        if not url.startswith('http'):
            InfoBar.warning(
                title="提示",
                content="请输入有效的URL链接",
                parent=self,
                position=InfoBarPosition.TOP,
                duration=2000
            )
            return
        
        output_dir = self.output_input.text().strip() or DEFAULT_OUTPUT_DIR
        os.makedirs(output_dir, exist_ok=True)
        
        # 重置UI
        self._reset_ui()
        
        # 显示进度
        self.progress_bar.show()
        self.progress_bar.setValue(0)
        self.extract_btn.hide()
        self.cancel_btn.show()
        self.open_folder_btn.hide()
        self.status_label.setText("正在提取...")
        
        # 启动工作线程
        self.worker = ImageExtractWorker(
            url=url,
            output_dir=output_dir,
            save_images=self.save_images_check.isChecked()
        )
        self.worker.progress_update.connect(self._on_progress_update)
        self.worker.image_found.connect(self._on_image_found)
        self.worker.extract_success.connect(self._on_extract_success)
        self.worker.extract_failed.connect(self._on_extract_failed)
        self.worker.download_progress.connect(self._on_download_progress)
        self.worker.download_complete.connect(self._on_download_complete)
        self.worker.start()
    
    def _on_cancel(self):
        """取消提取"""
        if self.worker:
            self.worker.cancel()
            self.worker = None
        
        self.extract_btn.show()
        self.cancel_btn.hide()
        self.progress_bar.hide()
        self.status_label.setText("已取消")
    
    def _on_open_folder(self):
        """打开输出文件夹"""
        if hasattr(self, '_output_folder') and self._output_folder:
            os.startfile(self._output_folder)
    
    def _reset_ui(self):
        """重置UI状态"""
        self.article_title_label.setText("提取中...")
        self.article_title_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        self.image_count_label.setText("0")
        self.image_list_text.clear()
        self._image_urls = []
    
    def _on_progress_update(self, current, total, message):
        """更新进度"""
        if total > 0:
            self.progress_bar.setValue(int(current * 100 / total))
        self.status_label.setText(message)
    
    def _on_image_found(self, index, url, alt):
        """发现图片"""
        self._image_urls.append((index, url, alt))
        self.image_count_label.setText(str(len(self._image_urls)))
        
        # 更新预览
        current_text = self.image_list_text.toPlainText()
        new_line = f"{index}. {url[:80]}{'...' if len(url) > 80 else ''}\n"
        self.image_list_text.setPlainText(current_text + new_line)
    
    def _on_download_progress(self, current, total, message):
        """下载进度"""
        # 下载阶段占70-100%
        progress = 70 + int(current * 30 / total)
        self.progress_bar.setValue(progress)
        self.status_label.setText(message)
    
    def _on_extract_success(self, title, images, md_content):
        """提取成功"""
        self.article_title_label.setText(title)
        self.article_title_label.setStyleSheet(f"color: {COLORS['success']};")
        self.image_count_label.setText(str(len(images)))
        
        self.extract_btn.show()
        self.cancel_btn.hide()
        self.progress_bar.setValue(100)
        
        # 播放任务完成音效
        play_sound('complete')
        
        InfoBar.success(
            title="提取成功",
            content=f"共提取 {len(images)} 张图片",
            parent=self,
            position=InfoBarPosition.TOP,
            duration=3000
        )
    
    def _on_extract_failed(self, error_msg):
        """提取失败"""
        self.extract_btn.show()
        self.cancel_btn.hide()
        self.progress_bar.hide()
        self.status_label.setText(f"失败: {error_msg}")
        self.status_label.setStyleSheet(f"color: {COLORS['error']};")
        
        InfoBar.error(
            title="提取失败",
            content=error_msg,
            parent=self,
            position=InfoBarPosition.TOP,
            duration=5000
        )
    
    def _on_download_complete(self, folder_path):
        """下载完成"""
        self._output_folder = folder_path
        self.open_folder_btn.show()
        self.status_label.setText(f"完成！文件已保存到: {folder_path}")
        self.status_label.setStyleSheet(f"color: {COLORS['success']};")
    
    def set_article_url(self, url: str):
        """设置文章链接（供外部调用）
        
        Args:
            url: 文章链接
        """
        self.url_input.setText(url)
        self.url_input.setFocus()