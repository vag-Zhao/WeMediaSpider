#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUI 工具函数模块

本模块提供 GUI 应用所需的各种工具函数和类，主要包括：

路径管理:
    - get_default_output_dir(): 获取默认输出目录（用户主目录下的 WeChatSpider）
    - get_app_data_dir(): 获取应用数据目录（存储配置和缓存）
    - get_cache_file_path(): 获取缓存文件的完整路径
    - get_wechat_cache_file(): 获取微信缓存文件路径
    - get_account_history_file(): 获取公众号历史记录文件路径

音频播放:
    - SoundPlayer: 音频播放器单例类
    - get_sound_player(): 获取全局播放器实例
    - play_sound(): 播放指定类型的音效

路径常量:
    - DEFAULT_OUTPUT_DIR: 默认输出目录
    - WECHAT_CACHE_FILE: 微信缓存文件路径
    - ACCOUNT_HISTORY_FILE: 公众号历史记录文件路径
    - SOUND_LOGIN: 登录成功音效路径
    - SOUND_EXPORT: 导出凭证音效路径
    - SOUND_COMPLETE: 任务完成音效路径

设计考虑:
    所有路径函数都考虑了跨平台兼容性（Windows/macOS/Linux）和权限问题。
    输出目录放在用户主目录下，避免安装到 Program Files 后的写入权限问题。
    应用数据目录遵循各平台的标准位置（AppData/Library/~/.local）。
"""

import os
import sys
from pathlib import Path
from PyQt6.QtCore import QUrl
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput


def get_default_output_dir() -> str:
    """获取默认输出目录
    
    返回用户主目录下的 WeChatSpider 文件夹路径。
    这样可以避免安装到 Program Files 后的权限问题。
    
    路径示例：
    - Windows: C:/Users/用户名/WeChatSpider
    - macOS: /Users/用户名/WeChatSpider
    - Linux: /home/用户名/WeChatSpider
    
    Returns:
        str: 默认输出目录的绝对路径
    """
    # 获取用户主目录
    if sys.platform == 'win32':
        # Windows: 使用 USERPROFILE
        user_home = os.environ.get('USERPROFILE', '')
        if not user_home:
            # 备选：使用 HOMEDRIVE + HOMEPATH
            home_drive = os.environ.get('HOMEDRIVE', 'C:')
            home_path = os.environ.get('HOMEPATH', '\\Users\\Default')
            user_home = home_drive + home_path
    else:
        # macOS/Linux: 使用 HOME 环境变量
        user_home = os.environ.get('HOME', os.path.expanduser('~'))
    
    # 创建 WeChatSpider 子目录（直接在用户主目录下）
    output_dir = os.path.join(user_home, 'WeChatSpider')
    
    # 确保目录存在
    try:
        os.makedirs(output_dir, exist_ok=True)
    except OSError:
        # 如果创建失败，回退到当前目录
        output_dir = os.path.abspath('results')
        os.makedirs(output_dir, exist_ok=True)
    
    return output_dir


def get_app_data_dir() -> str:
    """获取应用数据目录
    
    用于存储配置文件、缓存等应用数据。
    
    路径示例：
    - Windows: C:/Users/用户名/AppData/Local/WeChatSpider
    - macOS: ~/Library/Application Support/WeChatSpider
    - Linux: ~/.local/share/WeChatSpider
    
    Returns:
        str: 应用数据目录的绝对路径
    """
    if sys.platform == 'win32':
        # Windows: 使用 LOCALAPPDATA
        app_data = os.environ.get('LOCALAPPDATA', '')
        if not app_data:
            app_data = os.path.join(os.environ.get('USERPROFILE', ''), 'AppData', 'Local')
    elif sys.platform == 'darwin':
        # macOS: 使用 ~/Library/Application Support
        home = os.environ.get('HOME', os.path.expanduser('~'))
        app_data = os.path.join(home, 'Library', 'Application Support')
    else:
        # Linux: 使用 ~/.local/share
        home = os.environ.get('HOME', os.path.expanduser('~'))
        app_data = os.path.join(home, '.local', 'share')
    
    # 创建 WeChatSpider 子目录
    data_dir = os.path.join(app_data, 'WeChatSpider')
    
    # 确保目录存在
    try:
        os.makedirs(data_dir, exist_ok=True)
    except OSError:
        # 如果创建失败，回退到当前目录
        data_dir = os.path.abspath('.')
    
    return data_dir


def get_cache_file_path(filename: str) -> str:
    """获取缓存文件的完整路径
    
    将缓存文件保存到应用数据目录，避免权限问题。
    
    Args:
        filename: 缓存文件名，如 'wechat_cache.json'
        
    Returns:
        str: 缓存文件的完整路径
    """
    data_dir = get_app_data_dir()
    return os.path.join(data_dir, filename)


def get_wechat_cache_file() -> str:
    """获取微信缓存文件路径
    
    Returns:
        str: wechat_cache.json 的完整路径
    """
    return get_cache_file_path('wechat_cache.json')


def get_account_history_file() -> str:
    """获取公众号历史记录文件路径
    
    Returns:
        str: account_history.json 的完整路径
    """
    return get_cache_file_path('account_history.json')


# 导出默认输出目录常量（方便直接使用）
DEFAULT_OUTPUT_DIR = get_default_output_dir()

# 导出缓存文件路径常量
WECHAT_CACHE_FILE = get_wechat_cache_file()
ACCOUNT_HISTORY_FILE = get_account_history_file()


# ==================== 音频播放功能 ====================

def get_mic_dir() -> str:
    """获取音频文件目录
    
    Returns:
        str: mic 目录的绝对路径
    """
    # 获取项目根目录（gui/utils.py 的上两级目录）
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent
    mic_dir = project_root / 'mic'
    
    # 如果是打包后的程序，尝试从可执行文件目录查找
    if not mic_dir.exists():
        if getattr(sys, 'frozen', False):
            # PyInstaller 打包后的路径
            exe_dir = Path(sys.executable).parent
            mic_dir = exe_dir / 'mic'
    
    return str(mic_dir)


# 音频文件路径常量
MIC_DIR = get_mic_dir()
SOUND_LOGIN = os.path.join(MIC_DIR, 'login.mp3')      # 登录成功音效
SOUND_EXPORT = os.path.join(MIC_DIR, 'daochu.mp3')    # 导出凭证音效
SOUND_COMPLETE = os.path.join(MIC_DIR, 'over.mp3')    # 任务完成音效


class SoundPlayer:
    """音频播放器单例类
    
    使用 PyQt6 的 QMediaPlayer 播放音频文件。采用单例模式确保全局
    只有一个播放器实例，避免多个播放器同时播放造成的混乱。
    
    支持的音频格式取决于系统安装的解码器，通常包括 MP3、WAV、OGG 等。
    
    Attributes:
        _instance: 单例实例
        _player: QMediaPlayer 播放器实例
        _audio_output: QAudioOutput 音频输出实例
    
    使用示例:
        >>> player = SoundPlayer()
        >>> player.play('/path/to/sound.mp3')
        >>> player.set_volume(0.5)  # 设置音量为 50%
    
    注意:
        不要直接实例化此类，应使用 get_sound_player() 获取全局实例。
    """
    
    _instance = None
    _player = None
    _audio_output = None
    
    def __new__(cls):
        """创建或返回单例实例"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_player()
        return cls._instance
    
    def _init_player(self):
        """初始化播放器和音频输出
        
        创建 QMediaPlayer 和 QAudioOutput 实例，设置默认音量为 80%。
        如果初始化失败（例如系统不支持音频），会打印错误信息但不会抛出异常。
        """
        try:
            self._player = QMediaPlayer()
            self._audio_output = QAudioOutput()
            self._player.setAudioOutput(self._audio_output)
            self._audio_output.setVolume(0.8)  # 设置音量为80%
        except Exception as e:
            print(f"[SoundPlayer] 初始化播放器失败: {e}")
            self._player = None
            self._audio_output = None
    
    def play(self, sound_file: str):
        """播放音频文件
        
        如果当前正在播放其他音频，会先停止再播放新的。
        如果文件不存在或播放器未初始化，会静默失败并打印日志。
        
        Args:
            sound_file: 音频文件的绝对路径
        """
        if self._player is None:
            return
        
        if not os.path.exists(sound_file):
            print(f"[SoundPlayer] 音频文件不存在: {sound_file}")
            return
        
        try:
            # 停止当前播放
            self._player.stop()
            # 设置新的音频源
            self._player.setSource(QUrl.fromLocalFile(sound_file))
            # 开始播放
            self._player.play()
        except Exception as e:
            print(f"[SoundPlayer] 播放音频失败: {e}")
    
    def set_volume(self, volume: float):
        """设置播放音量
        
        Args:
            volume: 音量值，范围 0.0（静音）到 1.0（最大音量）
                   超出范围的值会被自动裁剪
        """
        if self._audio_output:
            self._audio_output.setVolume(max(0.0, min(1.0, volume)))


# 全局播放器实例
_sound_player = None


def get_sound_player() -> SoundPlayer:
    """获取全局音频播放器实例
    
    推荐使用此函数而不是直接实例化 SoundPlayer，
    以确保使用的是同一个播放器实例。
    
    Returns:
        全局唯一的 SoundPlayer 实例
    """
    global _sound_player
    if _sound_player is None:
        _sound_player = SoundPlayer()
    return _sound_player


def play_sound(sound_type: str):
    """播放指定类型的音效
    
    这是一个便捷函数，根据音效类型自动查找对应的音频文件并播放。
    
    Args:
        sound_type: 音效类型标识符，支持以下值：
            - 'login': 登录成功音效，用于微信登录成功时
            - 'export': 导出凭证音效，用于导出登录凭证时
            - 'complete': 任务完成音效，用于爬取任务完成时
    
    示例:
        >>> play_sound('login')   # 播放登录成功音效
        >>> play_sound('complete')  # 播放任务完成音效
    """
    sound_map = {
        'login': SOUND_LOGIN,
        'export': SOUND_EXPORT,
        'complete': SOUND_COMPLETE,
    }
    
    sound_file = sound_map.get(sound_type)
    if sound_file:
        player = get_sound_player()
        player.play(sound_file)
    else:
        print(f"[play_sound] 未知的音效类型: {sound_type}")