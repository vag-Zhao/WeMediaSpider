#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信公众平台登录模块
==================

实现微信公众平台的自动化登录流程，获取爬虫运行所需的认证信息。
采用 Selenium 驱动 Chrome 浏览器，用户扫码后自动提取 token 和 cookie。

工作流程:
    1. 启动 Chrome 浏览器并访问公众平台登录页
    2. 等待用户使用微信扫描二维码
    3. 检测登录成功后从 URL 提取 token
    4. 从浏览器获取 cookie 并保存到本地缓存
    5. 后续请求直接使用缓存，无需重复登录

缓存策略:
    - 登录信息保存在用户数据目录，避免权限问题
    - 默认缓存有效期 4 天（微信 token 通常 4-7 天过期）
    - 每次使用前自动验证缓存是否仍然有效
    - 支持手动清除缓存强制重新登录

安全考虑:
    - 使用临时目录存储浏览器数据，退出后自动清理
    - 隐藏 Selenium 自动化特征，降低被检测风险
    - 不在日志中输出完整的 token 和 cookie

依赖:
    - selenium: 浏览器自动化
    - requests: HTTP 请求（用于验证 token）
    - Chrome 浏览器和对应版本的 ChromeDriver
"""

import json
import os
import random
import time
import platform
import tempfile
import shutil
import subprocess
from datetime import datetime, timedelta

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
import re

from spider.log.utils import logger
from gui.utils import get_wechat_cache_file

# 缓存文件路径（存储在用户数据目录）
CACHE_FILE = get_wechat_cache_file()

# 缓存有效期：4 天（微信 token 一般 4-7 天过期）
CACHE_EXPIRE_HOURS = 24 * 4


class WeChatSpiderLogin:
    """
    微信公众平台登录管理器
    
    负责处理登录认证的完整生命周期，包括：
    - 缓存的读取、验证和保存
    - 浏览器的启动和配置
    - 登录流程的执行和监控
    - 资源的清理和释放
    
    Attributes:
        token: 访问令牌，用于 API 请求认证
        cookies: 会话 cookie 字典
        cache_file: 缓存文件路径
        cache_expire_hours: 缓存过期时间（小时）
        driver: Selenium WebDriver 实例
        temp_user_data_dir: 临时用户数据目录
    
    Example:
        >>> login = WeChatSpiderLogin()
        >>> if login.login():
        ...     token = login.get_token()
        ...     headers = login.get_headers()
        ...     # 使用 token 和 headers 进行爬取
    """

    def __init__(self, cache_file=CACHE_FILE):
        """
        初始化登录管理器
        
        Args:
            cache_file: 缓存文件路径，默认使用用户数据目录下的文件
        """
        self.token = None
        self.cookies = None
        self.cache_file = cache_file
        self.cache_expire_hours = CACHE_EXPIRE_HOURS
        self.driver = None
        self.temp_user_data_dir = None

    def save_cache(self):
        """
        保存登录信息到缓存文件
        
        将当前的 token 和 cookies 序列化为 JSON 格式保存，
        同时记录保存时间戳用于后续的过期检查。
        
        Returns:
            bool: 保存成功返回 True，失败返回 False
        """
        if self.token and self.cookies:
            cache_data = {
                'token': self.token,
                'cookies': self.cookies,
                'timestamp': datetime.now().timestamp()
            }
            try:
                with open(self.cache_file, 'w', encoding='utf-8') as f:
                    json.dump(cache_data, f, ensure_ascii=False, indent=2)
                logger.success(f"登录信息已保存到缓存文件 {self.cache_file}")
                return True
            except Exception as e:
                logger.error(f"保存缓存失败: {e}")
                return False
        return False

    def load_cache(self):
        """
        从缓存文件加载登录信息
        
        读取之前保存的 token 和 cookies，并检查是否过期。
        过期判断基于保存时的时间戳和配置的有效期。
        
        Returns:
            bool: 加载成功且未过期返回 True，否则返回 False
        """
        if not os.path.exists(self.cache_file):
            logger.info("缓存文件不存在，需要重新登录")
            return False
        
        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            cache_time = datetime.fromtimestamp(cache_data['timestamp'])
            current_time = datetime.now()
            hours_diff = (current_time - cache_time).total_seconds() / 3600
            
            if hours_diff > self.cache_expire_hours:
                logger.info(f"缓存已过期（{hours_diff:.1f}小时前），需要重新登录")
                return False
            
            self.token = cache_data['token']
            self.cookies = cache_data['cookies']
            logger.info(f"从缓存加载登录信息（{hours_diff:.1f}小时前保存）")
            return True
            
        except Exception as e:
            logger.error(f"读取缓存失败: {e}，需要重新登录")
            return False

    def validate_cache(self):
        """
        验证缓存的登录信息是否仍然有效
        
        通过发送一个测试请求到微信 API 来验证 token 是否有效。
        这比单纯检查时间戳更可靠，因为 token 可能被提前失效。
        
        Returns:
            bool: token 有效返回 True，无效返回 False
        
        Note:
            验证请求使用搜索公众号接口，这是一个轻量级的 API，
            不会产生实际的数据操作。
        """
        if not self.token or not self.cookies:
            return False
        
        try:
            headers = {
                "HOST": "mp.weixin.qq.com",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36"
            }
            
            test_url = 'https://mp.weixin.qq.com/cgi-bin/searchbiz'
            test_params = {
                'action': 'search_biz', 
                'token': self.token, 
                'lang': 'zh_CN', 
                'f': 'json', 
                'ajax': '1',
                'random': random.random(), 
                'query': 'test', 
                'begin': '0', 
                'count': '1',
            }
            
            response = requests.get(
                test_url, 
                cookies=self.cookies, 
                headers=headers, 
                params=test_params, 
                timeout=10
            )
            response.raise_for_status()

            result = response.json()
            
            if 'base_resp' in result:
                if result['base_resp']['ret'] == 0:
                    logger.success("缓存的登录信息验证有效")
                    return True
                elif result['base_resp']['ret'] in (-6, 200013):
                    logger.warning("缓存的token已失效")
                    return False
                else:
                    logger.warning(f"验证失败: {result['base_resp'].get('err_msg', '未知错误')}")
                    return False
            else:
                logger.warning("验证响应格式异常")
                return False
                
        except Exception as e:
            logger.error(f"验证缓存时发生错误: {e}")
            return False

    def clear_cache(self):
        """
        清除本地缓存文件
        
        删除保存的登录信息，下次使用时需要重新扫码登录。
        通常在 token 失效或需要切换账号时调用。
        
        Returns:
            bool: 清除成功返回 True，失败返回 False
        """
        try:
            if os.path.exists(self.cache_file):
                os.remove(self.cache_file)
                logger.info("缓存已清除")
            return True
        except Exception as e:
            logger.error(f"清除缓存失败: {e}")
            return False

    def _setup_chrome_options(self):
        """
        配置 Chrome 浏览器启动选项
        
        设置各种 Chrome 参数以优化爬虫场景下的表现：
        - 使用临时用户数据目录，避免影响用户的 Chrome 配置
        - 禁用不必要的功能以提升性能
        - 隐藏自动化特征以降低被检测风险
        - 调整页面缩放以适应不同分辨率
        
        Returns:
            webdriver.ChromeOptions: 配置好的选项对象
        """
        options = webdriver.ChromeOptions()
        
        # 创建临时目录保存用户数据
        self.temp_user_data_dir = tempfile.mkdtemp()
        options.add_argument(f"--user-data-dir={self.temp_user_data_dir}")
        
        # 其他选项
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-plugins")
        options.add_argument("--disable-software-rasterizer")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        # 页面缩放
        options.add_argument("--force-device-scale-factor=0.9")
        options.add_argument("--high-dpi-support=0.9")
        
        # 对无头模式的检测进行反规避
        options.add_argument("--disable-blink-features=AutomationControlled")
        
        # 自定义用户代理
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36")
        
        return options

    def _cleanup_chrome_processes(self):
        """
        清理残留的 Chrome 进程
        
        在某些异常情况下，Chrome 进程可能没有正常退出。
        这个方法会强制终止所有 Chrome 进程，确保资源被释放。
        
        Note:
            这是一个比较激进的清理方式，会影响所有 Chrome 进程，
            包括用户正在使用的浏览器。仅在必要时调用。
        """
        try:
            system = platform.system()
            if system == "Windows":
                subprocess.run(["taskkill", "/F", "/IM", "chrome.exe", "/T"], 
                              stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
            elif system in ("Linux", "Darwin"):  # Linux或Mac
                subprocess.run(["pkill", "-f", "chrome"], 
                              stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
            logger.debug("残留浏览器进程已清理")
        except Exception as e:
            logger.warning(f"清理Chrome进程时出现警告: {e}")

    def _cleanup_temp_files(self):
        """
        清理临时用户数据目录
        
        删除 Selenium 创建的临时目录，释放磁盘空间。
        这个目录包含浏览器的缓存、cookie 等数据。
        """
        if self.temp_user_data_dir and os.path.exists(self.temp_user_data_dir):
            try:
                shutil.rmtree(self.temp_user_data_dir, ignore_errors=True)
                logger.debug("临时用户数据目录已清理")
            except Exception as e:
                logger.warning(f"清理临时目录时出现警告: {e}")

    def login(self):
        """
        执行登录流程
        
        完整的登录流程包括：
        1. 检查本地缓存是否有效
        2. 如果缓存有效，直接使用缓存的登录信息
        3. 如果缓存无效，启动浏览器进行扫码登录
        4. 等待用户扫码并确认登录
        5. 提取 token 和 cookie 并保存到缓存
        
        Returns:
            bool: 登录成功返回 True，失败返回 False
        
        Note:
            扫码登录最长等待 5 分钟，超时后会返回失败。
            登录过程中会自动清理之前的残留进程和临时文件。
        """
        logger.info("\n" + "="*60)
        logger.info("开始登录微信公众号平台...")
        logger.info("="*60)
        
        # 检查缓存
        if self.load_cache() and self.validate_cache():
            logger.success("使用有效的缓存登录信息")
            return True
        else:
            logger.info("缓存无效或不存在，需要重新扫码登录")
            self.clear_cache()
        
        # 清理残留进程
        self._cleanup_chrome_processes()
        
        try:
            logger.info("正在启动Chrome浏览器...")
            
            # 配置Chrome选项
            chrome_options = self._setup_chrome_options()
            
            # 创建WebDriver
            try:
                service = ChromeService()
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                logger.success("Chrome浏览器启动成功")
            except Exception as e:
                logger.error(f"Chrome浏览器启动失败: {e}")
                return False

            # 隐藏自动化特征
            self.driver.execute_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )

            # 访问微信公众号平台
            logger.info("正在访问微信公众号平台...")
            self.driver.get('https://mp.weixin.qq.com/')
            logger.success("页面加载完成")
            
            logger.info("请在浏览器窗口中扫码登录...")
            logger.info("等待登录完成（最长等待5分钟）...")

            # 等待登录成功（URL中包含token）
            wait = WebDriverWait(self.driver, 300)  # 5分钟超时
            wait.until(EC.url_contains('token'))
            
            # 提取token
            current_url = self.driver.current_url
            logger.success("检测到登录成功！正在获取登录信息...")
            
            token_match = re.search(r'token=(\d+)', current_url)
            if token_match:
                self.token = token_match.group(1)
                logger.success(f"Token获取成功: {self.token}")
            else:
                logger.error("无法从URL中提取token")
                return False

            # 获取cookies
            raw_cookies = self.driver.get_cookies()
            self.cookies = {item['name']: item['value'] for item in raw_cookies}
            logger.success(f"Cookies获取成功，共{len(self.cookies)}个")
            
            # 保存到缓存
            if self.save_cache():
                logger.success("登录信息已保存到缓存")
            
            logger.success("登录完成！")
            return True
            
        except Exception as e:
            logger.error(f"登录过程中出现错误: {e}")
            return False
            
        finally:
            # 清理资源
            if self.driver:
                try:
                    self.driver.quit()
                    logger.debug("浏览器已关闭")
                except:
                    pass
            
            self._cleanup_chrome_processes()
            self._cleanup_temp_files()

    def check_login_status(self):
        """
        获取当前登录状态的详细信息
        
        返回一个包含登录状态各项指标的字典，可用于
        在界面上展示登录信息或判断是否需要重新登录。
        
        Returns:
            dict: 包含以下字段的状态信息
                - isLoggedIn: 是否已登录
                - loginTime: 登录时间（已登录时）
                - expireTime: 过期时间（已登录时）
                - hoursSinceLogin: 登录后经过的小时数
                - hoursUntilExpire: 距离过期的小时数
                - token: 当前 token（已登录时）
                - message: 状态描述文本
        """
        if self.load_cache() and self.validate_cache():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                cache_time = datetime.fromtimestamp(cache_data['timestamp'])
                expire_time = cache_time + timedelta(hours=self.cache_expire_hours)
                hours_since_login = (datetime.now() - cache_time).total_seconds() / 3600
                hours_until_expire = (expire_time - datetime.now()).total_seconds() / 3600
                
                return {
                    'isLoggedIn': True,
                    'loginTime': cache_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'expireTime': expire_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'hoursSinceLogin': round(hours_since_login, 1),
                    'hoursUntilExpire': round(hours_until_expire, 1),
                    'token': self.token,
                    'message': f'已登录 {round(hours_since_login, 1)} 小时'
                }
            except:
                pass
        
        return {
            'isLoggedIn': False,
            'message': '未登录或登录已过期'
        }

    def logout(self):
        """
        退出登录并清理所有相关资源
        
        执行以下清理操作：
        - 删除本地缓存文件
        - 清空内存中的 token 和 cookie
        - 终止残留的浏览器进程
        - 删除临时文件
        
        Returns:
            bool: 退出成功返回 True
        """
        logger.info("正在退出登录...")
        
        # 清除缓存和状态
        self.clear_cache()
        self.token = None
        self.cookies = None
        
        # 清理进程和临时文件
        self._cleanup_chrome_processes()
        self._cleanup_temp_files()
        
        logger.success("退出登录完成")
        return True

    def get_token(self):
        """
        获取访问令牌
        
        如果内存中没有 token，会尝试从缓存加载。
        
        Returns:
            str: 有效的 token 字符串，未登录时返回 None
        """
        if not self.token and not (self.load_cache() and self.validate_cache()):
            return None
        return self.token

    def get_cookies(self):
        """
        获取 cookie 字典
        
        返回的字典可以直接传递给 requests 库使用。
        
        Returns:
            dict: cookie 名称到值的映射，未登录时返回 None
        """
        if not self.cookies and not (self.load_cache() and self.validate_cache()):
            return None
        return self.cookies

    def get_cookie_string(self):
        """
        获取 HTTP 请求头格式的 cookie 字符串
        
        将 cookie 字典转换为 "name1=value1; name2=value2" 格式，
        可以直接设置到 HTTP 请求头的 Cookie 字段。
        
        Returns:
            str: 格式化的 cookie 字符串，未登录时返回 None
        """
        cookies = self.get_cookies()
        if not cookies:
            return None
        
        cookie_string = '; '.join([f"{key}={value}" for key, value in cookies.items()])
        return cookie_string

    def get_headers(self):
        """
        获取完整的 HTTP 请求头
        
        返回包含 cookie 和 User-Agent 的请求头字典，
        可以直接传递给 requests 库的 headers 参数。
        
        Returns:
            dict: 包含 cookie 和 user-agent 的请求头，未登录时返回 None
        """
        cookie_string = self.get_cookie_string()
        if not cookie_string:
            return None
        
        return {
            "cookie": cookie_string,
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36"
        }

    def is_logged_in(self):
        """
        快速检查是否处于登录状态
        
        这是一个便捷方法，内部调用 check_login_status()。
        
        Returns:
            bool: 已登录且 token 有效返回 True，否则返回 False
        """
        return self.check_login_status()['isLoggedIn']


def quick_login():
    """
    快速登录便捷函数
    
    创建登录管理器并执行登录，返回爬虫所需的认证信息。
    适合一次性使用场景，不需要保持登录管理器实例。
    
    Returns:
        tuple: (token, cookies, headers) 三元组
            - 登录成功: 返回有效的认证信息
            - 登录失败: 返回 (None, None, None)
    
    Example:
        >>> token, cookies, headers = quick_login()
        >>> if token:
        ...     # 登录成功，可以开始爬取
        ...     pass
    """
    login_manager = WeChatSpiderLogin()
    if login_manager.login():
        return (
            login_manager.get_token(),
            login_manager.get_cookies(),
            login_manager.get_headers()
        )
    return (None, None, None)


def check_login():
    """
    检查登录状态便捷函数
    
    快速获取当前的登录状态，无需手动创建登录管理器。
    
    Returns:
        dict: 登录状态信息字典，包含 isLoggedIn、message 等字段
    """
    login_manager = WeChatSpiderLogin()
    return login_manager.check_login_status() 