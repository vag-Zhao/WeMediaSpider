#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信公众号爬虫工具函数
====================

提供爬虫核心功能所需的底层工具函数，包括 HTTP 请求封装、
HTML 内容解析、数据格式转换等。这些函数被 scraper 模块调用，
也可以单独使用。

功能分类:
    API 请求:
        - get_fakid: 搜索公众号获取 fakeid
        - get_articles_list: 获取文章列表
        - get_article_content: 获取文章正文
    
    内容解析:
        - _preprocess_lazy_images: 处理懒加载图片
        - _extract_image_article_content: 提取图片类文章
        - _extract_fallback_content: 备用内容提取
    
    数据转换:
        - get_timestamp / format_time: 时间戳格式化
        - filter_by_keywords: 关键词过滤
        - save_to_csv: CSV 文件保存

技术说明:
    - 使用 requests 发送同步 HTTP 请求
    - 使用 BeautifulSoup + lxml 解析 HTML
    - 使用 markdownify 将 HTML 转换为 Markdown
    - 内置请求频率控制，避免触发反爬机制
"""

import requests
import random
import time
import os
import csv
from datetime import datetime

from tqdm import tqdm
import bs4
from markdownify import MarkdownConverter

from spider.log.utils import logger


class ImageBlockConverter(MarkdownConverter):
    """
    自定义 Markdown 转换器
    
    继承 markdownify 的转换器，重写图片处理逻辑，
    使图片在 Markdown 中独占一行，提升可读性。
    
    主要改动:
        - 图片前后添加换行符
        - 优先使用 data-src 属性（微信懒加载图片）
    """
    
    def convert_img(self, el, text, parent_tags):
        """
        转换 img 标签为 Markdown 图片语法
        
        Args:
            el: BeautifulSoup 的 img 元素
            text: 元素的文本内容（图片通常为空）
            parent_tags: 父级标签集合
        
        Returns:
            str: Markdown 格式的图片文本，如 ![alt](src)
        """
        alt = el.attrs.get('alt', None) or ''
        src = el.attrs.get('src', None) or ''
        if not src:
            src = el.attrs.get('data-src', None) or ''
        title = el.attrs.get('title', None) or ''
        title_part = ' "%s"' % title.replace('"', r'\"') if title else ''
        if ('_inline' in parent_tags
                and el.parent.name not in self.options['keep_inline_images_in']):
            return alt

        return '\n![%s](%s%s)\n' % (alt, src, title_part)


def md(soup, **options):
    """
    将 BeautifulSoup 对象转换为 Markdown 文本
    
    这是 ImageBlockConverter 的便捷调用方法。
    
    Args:
        soup: BeautifulSoup 对象或元素
        **options: 传递给转换器的选项
    
    Returns:
        str: 转换后的 Markdown 文本
    """
    return ImageBlockConverter(**options).convert_soup(soup)


def get_fakid(headers, tok, query):
    """
    搜索公众号并获取 fakeid
    
    fakeid 是微信公众平台内部使用的公众号唯一标识，
    后续获取文章列表等操作都需要用到这个 ID。
    
    Args:
        headers: HTTP 请求头，必须包含有效的 cookie
        tok: 访问令牌（token）
        query: 搜索关键词，通常是公众号名称
    
    Returns:
        list[dict]: 匹配的公众号列表，每项包含:
            - wpub_name: 公众号名称
            - wpub_fakid: 公众号的 fakeid
    
    Example:
        >>> results = get_fakid(headers, token, '人民日报')
        >>> print(results[0]['wpub_fakid'])
    """
    url = 'https://mp.weixin.qq.com/cgi-bin/searchbiz'
    data = {
        'action': 'search_biz',
        'scene': 1,
        'begin': 0,
        'count': 10,
        'query': query,
        'token': tok,
        'lang': 'zh_CN',
        'f': 'json',
        'ajax': '1',
    }
    
    # 发送请求
    r = requests.get(url, headers=headers, params=data)
    
    # 解析json
    dic = r.json()
    
    # 获取公众号名称、fakeid
    wpub_list = [
        {
            'wpub_name': item['nickname'],
            'wpub_fakid': item['fakeid']
        }
        for item in dic['list']
    ]
    
    return wpub_list


def get_articles_list(page_num, start_page, fakeid, token, headers):
    """
    分页获取公众号的历史文章列表
    
    通过微信公众平台的 API 获取指定公众号的文章列表。
    每页固定返回 5 篇文章，函数会自动处理分页逻辑。
    
    Args:
        page_num: 要获取的页数（每页 5 篇）
        start_page: 起始偏移量（0 表示从第一篇开始）
        fakeid: 目标公众号的 fakeid
        token: 访问令牌
        headers: HTTP 请求头
    
    Returns:
        tuple: 三个列表组成的元组
            - titles: 文章标题列表
            - links: 文章链接列表
            - update_times: 发布时间戳列表
    
    Note:
        函数内置 1-2 秒的随机延迟，避免请求过快被封禁。
        使用 tqdm 显示进度条。
    """
    url = 'https://mp.weixin.qq.com/cgi-bin/appmsg'
    title = []
    link = []
    update_time = []
    
    with tqdm(total=page_num) as pbar:
        for i in range(page_num):
            data = {
                'action': 'list_ex',
                'begin': start_page + i*5,       #页数
                'count': '5',
                'fakeid': fakeid,
                'type': '9',
                'query':'',
                'token': token,
                'lang': 'zh_CN',
                'f': 'json',
                'ajax': '1',
            }
            
            # 随机延时，避免被反爬
            time.sleep(random.randint(1, 2))
            
            r = requests.get(url, headers=headers, params=data)
            # 解析json
            dic = r.json()
            
            # 调试日志：打印API响应
            logger.info(f"API响应状态: {r.status_code}")
            if 'base_resp' in dic:
                logger.info(f"base_resp: {dic['base_resp']}")
            logger.info(f"app_msg_cnt: {dic.get('app_msg_cnt', 'N/A')}, 本页文章数: {len(dic.get('app_msg_list', []))}")
            
            # 检查是否有文章列表
            if 'app_msg_list' not in dic:
                logger.warning(f"未找到文章列表, 响应为: {dic}")
                break
                
            for item in dic['app_msg_list']:
                title.append(item['title'])      # 获取标题
                link.append(item['link'])        # 获取链接
                update_time.append(item['update_time'])  # 获取更新时间戳
                
            pbar.update(1)
    
    return title, link, update_time


def _preprocess_lazy_images(soup):
    """
    预处理微信文章中的懒加载图片
    
    微信文章的图片使用懒加载技术，真实 URL 存储在 data-src 属性中，
    src 属性通常是一个占位符（SVG 或空白图片）。这个函数将 data-src
    的值复制到 src，使后续的 Markdown 转换能正确处理图片。
    
    Args:
        soup: BeautifulSoup 对象，会被原地修改
    """
    for img in soup.find_all('img'):
        # 检查src是否是占位符（SVG或空）
        src = img.get('src', '')
        data_src = img.get('data-src', '')
        
        # 如果src是SVG占位符或为空，且data-src有值，则替换
        if data_src and (not src or 'data:image/svg' in src or 'pic_blank' in src):
            img['src'] = data_src
            logger.debug(f"替换懒加载图片: {data_src[:50]}...")


def _extract_fallback_content(soup, content_ele):
    """
    备用内容提取方法
    
    当标准的 Markdown 转换失败或结果不理想时使用。
    采用更简单直接的方式提取文本和图片，确保不会丢失内容。
    
    Args:
        soup: 完整页面的 BeautifulSoup 对象
        content_ele: 文章内容区域的元素
    
    Returns:
        str: 提取的内容，Markdown 格式
    """
    content_parts = []
    
    # 1. 提取标题
    title_ele = soup.select_one('.rich_media_title, #activity-name, h1')
    if title_ele and title_ele.get_text(strip=True):
        content_parts.append(f"# {title_ele.get_text(strip=True)}\n")
    
    # 2. 提取文本内容
    if content_ele:
        text_content = content_ele.get_text(separator='\n', strip=True)
        if text_content:
            content_parts.append(f"\n{text_content}\n")
    
    # 3. 提取所有图片
    if content_ele:
        images = content_ele.find_all('img')
        if images:
            content_parts.append("\n## 图片\n")
            for i, img in enumerate(images, 1):
                src = img.get('src') or img.get('data-src') or ''
                alt = img.get('alt') or f'图片{i}'
                # 过滤掉占位符图片
                if src and 'mmbiz.qpic.cn' in src and 'data:image' not in src:
                    content_parts.append(f"\n![{alt}]({src})\n")
    
    return ''.join(content_parts) if content_parts else None


def get_article_content(url, headers, max_retries=3, retry_delay=2):
    """
    获取文章正文内容并转换为 Markdown
    
    访问文章页面，解析 HTML 提取正文内容，然后转换为 Markdown 格式。
    支持多种文章类型：普通图文、纯图片、视频等。
    
    Args:
        url: 文章的完整 URL
        headers: HTTP 请求头，需要包含有效的 cookie
        max_retries: 请求失败时的最大重试次数
        retry_delay: 重试之间的等待时间（秒），会逐次增加
    
    Returns:
        str: Markdown 格式的文章内容，失败时返回错误信息
    
    内容选择器优先级:
        1. .rich_media_content - 标准图文文章
        2. #js_content - 标准文章（ID 选择器）
        3. #js_image_content - 图片类文章
        4. 其他备用选择器...
    
    Note:
        对于图片类文章（page_share_img），会使用专门的提取逻辑。
        如果所有方法都失败，会尝试提取页面的纯文本内容。
    """
    # 定义多个可能的内容选择器，按优先级排序
    # 支持普通图文文章、图片类文章、视频类文章等多种类型
    CONTENT_SELECTORS = [
        # === 普通图文文章 ===
        ".rich_media_content",           # 标准文章内容（最常见）
        "#js_content",                   # 标准文章内容（ID选择器）
        
        # === 图片类文章（page_share_img）===
        "#js_image_content",             # 图片类文章主容器
        ".image_content",                # 图片类文章内容区
        "#js_image_desc",                # 图片类文章描述
        ".share_notice",                 # 图片类文章分享提示
        
        # === 图片轮播组件 ===
        ".swiper_item_img",              # 轮播图片项
        "#img_swiper_content",           # 轮播内容容器
        ".share_media_swiper_content",   # 轮播媒体内容
        ".img_swiper_area",              # 轮播区域
        
        # === 视频类文章 ===
        "#js_video_content",             # 视频类文章内容
        ".video_content",                # 视频内容区
        ".rich_media_video",             # 视频媒体区
        
        # === 其他内容区域 ===
        ".rich_media_area_primary",      # 主要内容区域
        ".rich_media_area_primary_inner",# 主要内容区域内部
        "#js_article_content",           # 文章内容容器
        "#js_content_container",         # 内容容器
        
        # === 备用选择器 ===
        "#page-content",                 # 页面内容
        ".rich_media_inner",             # 富媒体内部
        ".rich_media_wrp",               # 富媒体包装
        "article",                       # HTML5 article标签
        ".article",                      # 文章类
        "#article",                      # 文章ID
    ]
    
    # 内容有效性检测的最小长度阈值
    MIN_CONTENT_LENGTH = 10
    
    for attempt in range(max_retries):
        try:
            # 发送请求，增加超时设置
            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code != 200:
                logger.warning(f"请求失败，状态码: {response.status_code}，尝试 {attempt + 1}/{max_retries}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                return f"请求失败，状态码: {response.status_code}"
            
            # 解析HTML
            soup = bs4.BeautifulSoup(response.text, 'lxml')
            
            # 预处理懒加载图片
            _preprocess_lazy_images(soup)
            
            # 检测文章类型
            body_classes = soup.body.get('class', []) if soup.body else []
            is_image_article = 'page_share_img' in body_classes
            
            # 检测是否有图片轮播组件（swiper）
            has_swiper = bool(soup.select('.swiper_item, .swiper_item_img, .share_media_swiper'))
            
            if is_image_article or has_swiper:
                logger.info(f"检测到图片类型文章（page_share_img={is_image_article}, swiper={has_swiper}），使用特殊处理")
                content = _extract_image_article_content(soup)
                if content and len(content.strip()) >= MIN_CONTENT_LENGTH:
                    return content
            
            # 尝试多个选择器
            content_ele = None
            used_selector = None
            for selector in CONTENT_SELECTORS:
                content_ele = soup.select(selector)
                if content_ele:
                    used_selector = selector
                    logger.debug(f"使用选择器 '{selector}' 匹配到内容元素")
                    break
            
            content = ""
            if content_ele:
                # 将HTML转换为Markdown
                content = md(content_ele[0], keep_inline_images_in=["section", "span"])
                
                # 验证内容是否有效（去除空白后长度大于阈值）
                content_stripped = content.strip()
                if len(content_stripped) < MIN_CONTENT_LENGTH:
                    logger.warning(f"Markdown转换后内容过短({len(content_stripped)}字符)，尝试备用提取方法")
                    fallback_content = _extract_fallback_content(soup, content_ele[0])
                    if fallback_content and len(fallback_content.strip()) > len(content_stripped):
                        content = fallback_content
                        logger.info("使用备用提取方法成功获取内容")
            
            # 检查内容是否有效
            if content and len(content.strip()) >= MIN_CONTENT_LENGTH:
                logger.info(f"成功获取文章内容，长度: {len(content.strip())} 字符")
                return content
            
            # 内容为空或过短，可能是页面未完全加载，进行重试
            if attempt < max_retries - 1:
                logger.warning(f"内容为空或过短，可能页面未完全加载，{retry_delay}秒后重试 ({attempt + 1}/{max_retries})")
                time.sleep(retry_delay)
                # 增加重试延迟，给页面更多加载时间
                retry_delay = min(retry_delay * 1.5, 10)
            else:
                # 最后一次尝试，返回已获取的内容（即使为空）
                logger.warning(f"重试{max_retries}次后仍无法获取有效内容，URL: {url}")
                if not content:
                    # 尝试最后的备用方法：提取所有文本
                    content = _extract_all_text_content(soup)
                return content
                
        except requests.exceptions.Timeout:
            logger.warning(f"请求超时，尝试 {attempt + 1}/{max_retries}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                return "获取文章内容失败: 请求超时"
        except requests.exceptions.RequestException as e:
            logger.warning(f"请求异常: {e}，尝试 {attempt + 1}/{max_retries}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                return f"获取文章内容失败: {str(e)}"
        except Exception as e:
            logger.error(f"获取文章内容时发生异常: {e}")
            return f"获取文章内容失败: {str(e)}"
    
    return ""


def _extract_all_text_content(soup):
    """
    最后的兜底方法：提取页面所有可见文本
    
    当其他所有提取方法都失败时使用。会尝试获取标题、
    正文文本和图片，确保不会返回完全空的内容。
    
    Args:
        soup: BeautifulSoup 对象
    
    Returns:
        str: 提取的文本内容，Markdown 格式
    """
    content_parts = []
    
    # 尝试获取标题
    title_ele = soup.select_one('.rich_media_title, #activity-name, h1')
    if title_ele and title_ele.get_text(strip=True):
        content_parts.append(f"# {title_ele.get_text(strip=True)}\n")
    
    # 尝试获取主要内容区域的文本
    main_content_selectors = [
        '.rich_media_content',
        '#js_content',
        '.rich_media_area_primary',
        'article',
        '.article-content'
    ]
    
    for selector in main_content_selectors:
        ele = soup.select_one(selector)
        if ele:
            text = ele.get_text(separator='\n', strip=True)
            if text and len(text) > 20:
                content_parts.append(f"\n{text}\n")
                break
    
    # 提取所有图片
    images = soup.select('img[data-src], img[src*="mmbiz.qpic.cn"]')
    if images:
        content_parts.append("\n## 图片\n")
        for i, img in enumerate(images[:20], 1):  # 限制最多20张图片
            src = img.get('data-src') or img.get('src') or ''
            if src and 'mmbiz.qpic.cn' in src and 'data:image' not in src:
                alt = img.get('alt') or f'图片{i}'
                content_parts.append(f"\n![{alt}]({src})\n")
    
    return ''.join(content_parts) if content_parts else ""


def _decode_html_entities(text):
    """
    解码 HTML 实体和 JavaScript 转义字符
    
    处理微信文章中常见的编码问题：
    - HTML 实体：&amp; -> &, &lt; -> <
    - 十六进制转义：\\x26 -> &
    - 双重编码的情况
    
    Args:
        text: 可能包含编码字符的文本
    
    Returns:
        str: 解码后的纯文本
    """
    import html
    if not text:
        return text
    
    # 解码HTML实体（如 &amp; -> &, &lt; -> <）
    text = html.unescape(text)
    
    # 处理双重转义的情况（如 \x26lt; -> &lt; -> <）
    # 先处理 \x26 这种十六进制转义
    import re
    def replace_hex_escape(match):
        hex_val = match.group(1)
        try:
            return chr(int(hex_val, 16))
        except:
            return match.group(0)
    
    text = re.sub(r'\\x([0-9a-fA-F]{2})', replace_hex_escape, text)
    
    # 再次解码HTML实体（处理双重转义后的结果）
    text = html.unescape(text)
    
    return text


def _extract_image_article_content(soup):
    """
    提取图片类型文章的内容
    
    专门处理微信的图片类文章（page_share_img 类型），这类文章
    的图片通常存储在 JavaScript 变量或特殊的 HTML 结构中。
    
    提取策略（按优先级）：
        1. 从 JavaScript 变量 picture_page_info_list 提取
        2. 从 swiper_item 容器的 data-src 属性提取
        3. 从 img 标签提取
        4. 从 style 属性中的背景图片提取
    
    Args:
        soup: BeautifulSoup 对象
    
    Returns:
        str: Markdown 格式的内容，包含标题、描述和图片
    """
    content_parts = []
    seen_urls = set()  # 用于去重
    
    def add_image(src, alt=''):
        """添加图片到内容列表"""
        if not src:
            return
        # 解码URL中的HTML实体
        src = _decode_html_entities(src)
        # 标准化URL用于去重
        base_url = src.split('?')[0] if '?' in src else src
        if base_url in seen_urls:
            return
        if 'mmbiz.qpic.cn' not in src:
            return
        if 'pic_blank' in src or 'data:image' in src:
            return
        seen_urls.add(base_url)
        alt = alt or f'图片{len(seen_urls)}'
        content_parts.append(f"\n![{alt}]({src})\n")
    
    # 1. 提取标题
    title_selectors = ['.rich_media_title', '#activity-name', '#js_image_content h1', 'h1']
    for selector in title_selectors:
        title_ele = soup.select_one(selector)
        if title_ele and title_ele.get_text(strip=True):
            title_text = _decode_html_entities(title_ele.get_text(strip=True))
            content_parts.append(f"# {title_text}\n")
            break
    
    # 2. 提取描述/摘要
    desc_selectors = ['#js_image_desc', '.share_notice', 'meta[name="description"]']
    for selector in desc_selectors:
        if selector.startswith('meta'):
            desc_ele = soup.select_one(selector)
            if desc_ele and desc_ele.get('content'):
                desc_text = _decode_html_entities(desc_ele.get('content'))
                content_parts.append(f"\n{desc_text}\n")
                break
        else:
            desc_ele = soup.select_one(selector)
            if desc_ele and desc_ele.get_text(strip=True):
                desc_text = _decode_html_entities(desc_ele.get_text(strip=True))
                content_parts.append(f"\n{desc_text}\n")
                break
    
    # 3. 从 JavaScript 变量中提取图片（最可靠的方法）
    js_images_found = False
    for script in soup.find_all('script'):
        script_text = script.string or ''
        if 'picture_page_info_list' in script_text:
            import re
            import json
            match = re.search(r'var\s+picture_page_info_list\s*=\s*(\[[\s\S]*?\]);', script_text)
            if match:
                try:
                    json_str = match.group(1)
                    json_str = _decode_html_entities(json_str)
                    pic_list = json.loads(json_str)
                    
                    if pic_list:
                        content_parts.append("\n## 图片内容\n")
                        for pic_info in pic_list:
                            cdn_url = pic_info.get('cdn_url', '')
                            if cdn_url:
                                cdn_url = _decode_html_entities(cdn_url)
                                add_image(cdn_url)
                        js_images_found = True
                except (json.JSONDecodeError, Exception) as e:
                    logger.debug(f"解析 picture_page_info_list 失败: {e}")
    
    # 4. 如果JS方法没找到图片，尝试从 swiper_item 容器的 data-src 属性提取
    if not js_images_found or len(seen_urls) == 0:
        # 方法4a: 从 swiper_item 容器的 data-src 属性提取（新的HTML结构）
        swiper_items = soup.select('.swiper_item[data-src], div[data-src*="mmbiz.qpic.cn"]')
        if swiper_items:
            if not js_images_found:
                content_parts.append("\n## 图片内容\n")
            for item in swiper_items:
                src = item.get('data-src', '')
                if src:
                    add_image(src)
        
        # 方法4b: 从 swiper_item_img 内的 img 标签提取
        swiper_images = soup.select('.swiper_item_img img')
        if swiper_images:
            if not js_images_found and len(seen_urls) == 0:
                content_parts.append("\n## 图片内容\n")
            for img in swiper_images:
                src = img.get('src') or img.get('data-src') or ''
                alt = img.get('alt') or ''
                add_image(src, alt)
        
        # 方法4c: 从其他图片容器提取
        if len(seen_urls) == 0:
            other_selectors = [
                '#js_image_content img',
                '.image_content img',
                '.wx_img_swiper img',
                '.img_swiper_wrp img'
            ]
            for selector in other_selectors:
                images = soup.select(selector)
                if images:
                    if len(seen_urls) == 0:
                        content_parts.append("\n## 图片内容\n")
                    for img in images:
                        src = img.get('src') or img.get('data-src') or ''
                        alt = img.get('alt') or ''
                        add_image(src, alt)
                    if len(seen_urls) > 0:
                        break
    
    # 5. 通用兜底方法：提取所有 mmbiz.qpic.cn 域名的图片
    # 这是最后的保障，确保不会遗漏任何图片
    if len(seen_urls) == 0:
        logger.info("使用通用兜底方法提取所有微信图片")
        content_parts.append("\n## 图片内容\n")
        
        # 方法5a: 提取所有带有 mmbiz.qpic.cn 的 img 标签
        all_images = soup.find_all('img')
        for img in all_images:
            # 尝试从多个属性获取图片URL
            src = img.get('src') or img.get('data-src') or img.get('data-original') or ''
            alt = img.get('alt') or ''
            if src:
                add_image(src, alt)
        
        # 方法5b: 提取所有带有 data-src 属性且包含 mmbiz.qpic.cn 的元素（不仅仅是img）
        elements_with_data_src = soup.find_all(attrs={'data-src': True})
        for ele in elements_with_data_src:
            src = ele.get('data-src', '')
            if src:
                add_image(src)
        
        # 方法5c: 从 style 属性中提取背景图片URL
        import re as regex_module
        elements_with_style = soup.find_all(style=True)
        for ele in elements_with_style:
            style = ele.get('style', '')
            # 匹配 background-image: url(...) 或 background: url(...)
            bg_matches = regex_module.findall(r'url\(["\']?(https?://mmbiz\.qpic\.cn[^"\')\s]+)["\']?\)', style)
            for bg_url in bg_matches:
                add_image(bg_url)
    
    # 6. 提取话题标签（清理HTML标签）
    import re
    topic_links = soup.select('.wx_topic_link')
    if topic_links:
        topics = []
        for link in topic_links:
            topic_text = link.get_text(strip=True)
            if topic_text:
                # 清理话题文本
                topic_text = _decode_html_entities(topic_text)
                # 移除可能残留的HTML标签
                topic_text = re.sub(r'<[^>]+>', '', topic_text)
                if topic_text and not topic_text.startswith('<'):
                    topics.append(topic_text)
        if topics:
            content_parts.append(f"\n**话题标签**: {' '.join(topics)}\n")
    
    return ''.join(content_parts) if content_parts else None


def get_timestamp(update_time):
    """
    将 UNIX 时间戳转换为可读的日期时间字符串
    
    Args:
        update_time: UNIX 时间戳（秒）
    
    Returns:
        str: 格式化的时间字符串，如 "2024-01-15 14:30:00"
             转换失败时返回错误信息
    """
    try:
        dt = datetime.fromtimestamp(int(update_time))
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except Exception as e:
        return f"时间戳转换失败: {str(e)}"


def format_time(timestamp):
    """
    格式化时间戳（简化版）
    
    与 get_timestamp 功能相同，但失败时返回空字符串而非错误信息。
    适合在不需要错误提示的场景使用。
    
    Args:
        timestamp: UNIX 时间戳（秒）
    
    Returns:
        str: 格式化的时间字符串，失败时返回空字符串
    """
    try:
        dt = datetime.fromtimestamp(int(timestamp))
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        return ''


def filter_by_keywords(articles, keywords, field='title'):
    """
    根据关键词过滤文章列表
    
    检查文章的指定字段是否包含任意一个关键词，
    返回匹配的文章。匹配时不区分大小写。
    
    Args:
        articles: 文章字典列表
        keywords: 关键词列表，匹配任意一个即可
        field: 要搜索的字段名，默认为 'title'
    
    Returns:
        list: 包含关键词的文章列表
    
    Example:
        >>> articles = [{'title': 'Python教程'}, {'title': 'Java入门'}]
        >>> filter_by_keywords(articles, ['Python'])
        [{'title': 'Python教程'}]
    """
    if not keywords:
        return articles
    
    filtered = []
    for article in articles:
        if field not in article:
            continue
            
        content = article[field].lower()
        if any(keyword.lower() in content for keyword in keywords):
            filtered.append(article)
            
    return filtered


def save_to_csv(data, filename, fieldnames=None):
    """
    将数据保存到 CSV 文件
    
    支持自动创建目录、自动推断字段名、UTF-8 BOM 编码（Excel 兼容）。
    
    Args:
        data: 字典列表，每个字典代表一行数据
        filename: 输出文件路径
        fieldnames: CSV 列名列表，为 None 时从数据自动获取
    
    Returns:
        bool: 保存成功返回 True，失败返回 False
    """
    if not data:
        return False
        
    # 如果未提供字段名，尝试从数据中获取
    if not fieldnames:
        if isinstance(data[0], dict):
            fieldnames = list(data[0].keys())
        else:
            logger.error(f"保存CSV失败: 未提供字段名且无法自动获取")
            return False
    
    try:
        # 创建目录
        os.makedirs(os.path.dirname(filename) or '.', exist_ok=True)
        
        # 写入CSV
        with open(filename, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        
        logger.info(f"数据已保存到: {filename}")
        return True
    except Exception as e:
        logger.error(f"保存CSV失败: {str(e)}")
        return False


def mkdir(path):
    """
    创建目录（如果不存在）
    
    递归创建目录，如果目录已存在则不做任何操作。
    
    Args:
        path: 目录路径
    
    Returns:
        bool: 操作成功返回 True
    """
    # 去除首尾空格
    path = path.strip()
    
    # 判断路径是否存在
    if not path or os.path.exists(path):
        logger.info(f"{path} 目录已存在")
        return True
    
    # 创建目录
    os.makedirs(path)
    logger.info(f"{path} 创建成功")
    return True 