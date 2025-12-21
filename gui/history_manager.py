#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
公众号历史记录管理模块

本模块提供公众号搜索历史的持久化存储和管理功能。
历史记录保存在用户数据目录下的 JSON 文件中，避免权限问题。

主要功能:
    - 自动记录用户搜索过的公众号
    - 按最近使用时间排序
    - 限制最大记录数量
    - 支持添加、删除、清空操作

数据格式:
    历史记录以 JSON 格式存储，结构如下：
    {
        "accounts": [
            {"name": "公众号名称", "last_used": "2024-01-01T12:00:00"},
            ...
        ],
        "max_history": 20
    }

存储位置:
    - Windows: %LOCALAPPDATA%/WeChatSpider/account_history.json
    - macOS: ~/Library/Application Support/WeChatSpider/account_history.json
    - Linux: ~/.local/share/WeChatSpider/account_history.json

使用方式:
    >>> from gui.history_manager import get_history_manager
    >>> manager = get_history_manager()
    >>> manager.add_account("人民日报")
    >>> accounts = manager.get_accounts()
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Optional

from gui.utils import get_account_history_file

# 历史记录文件路径
HISTORY_FILE = get_account_history_file()

# 默认最大历史记录数
DEFAULT_MAX_HISTORY = 20


class AccountHistoryManager:
    """公众号历史记录管理器
    
    采用单例模式，确保全局只有一个管理器实例。
    负责历史记录的加载、保存、添加、删除等操作。
    历史记录按最近使用时间排序，最新使用的排在最前面。
    
    Attributes:
        _history_file: 历史记录文件路径
        _max_history: 最大历史记录数
        _accounts: 历史记录列表，每项包含 name 和 last_used
    
    示例:
        >>> manager = AccountHistoryManager()
        >>> manager.add_account("人民日报")
        >>> manager.add_account("新华社")
        >>> print(manager.get_accounts())
        ['新华社', '人民日报']  # 最近添加的在前
    """
    
    _instance = None
    
    def __new__(cls):
        """创建或返回单例实例"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """初始化管理器，加载历史记录文件"""
        if self._initialized:
            return
        self._initialized = True
        self._history_file = HISTORY_FILE
        self._max_history = DEFAULT_MAX_HISTORY
        self._accounts: List[Dict] = []
        self._load()
    
    def _load(self):
        """从文件加载历史记录
        
        如果文件不存在或格式错误，会初始化为空列表。
        兼容旧版本的纯字符串列表格式。
        """
        if not os.path.exists(self._history_file):
            self._accounts = []
            return
        
        try:
            with open(self._history_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self._accounts = data.get('accounts', [])
            self._max_history = data.get('max_history', DEFAULT_MAX_HISTORY)
            
            # 确保数据格式正确
            valid_accounts = []
            for acc in self._accounts:
                if isinstance(acc, dict) and 'name' in acc:
                    valid_accounts.append(acc)
                elif isinstance(acc, str):
                    # 兼容旧格式
                    valid_accounts.append({
                        'name': acc,
                        'last_used': datetime.now().isoformat()
                    })
            self._accounts = valid_accounts[:self._max_history]
            
        except Exception as e:
            print(f"加载历史记录失败: {e}")
            self._accounts = []
    
    def _save(self):
        """保存历史记录到文件
        
        使用 UTF-8 编码和缩进格式保存，便于调试查看。
        """
        try:
            data = {
                'accounts': self._accounts,
                'max_history': self._max_history
            }
            with open(self._history_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存历史记录失败: {e}")
    
    def get_accounts(self) -> List[str]:
        """获取所有历史公众号名称列表
        
        Returns:
            公众号名称列表，按最近使用时间排序（最新的在前）
        """
        return [acc['name'] for acc in self._accounts]
    
    def get_account_details(self) -> List[Dict]:
        """获取所有历史公众号的详细信息
        
        Returns:
            字典列表，每项包含：
            - name: 公众号名称
            - last_used: 最近使用时间（ISO 格式字符串）
        """
        return self._accounts.copy()
    
    def add_account(self, name: str):
        """添加公众号到历史记录
        
        如果公众号已存在，会更新其最近使用时间并移到列表最前面。
        如果超过最大记录数，会自动删除最旧的记录。
        
        Args:
            name: 公众号名称，空字符串会被忽略
        """
        if not name or not name.strip():
            return
        
        name = name.strip()
        
        # 检查是否已存在
        existing_index = None
        for i, acc in enumerate(self._accounts):
            if acc['name'] == name:
                existing_index = i
                break
        
        # 如果存在，先移除
        if existing_index is not None:
            self._accounts.pop(existing_index)
        
        # 添加到最前面
        self._accounts.insert(0, {
            'name': name,
            'last_used': datetime.now().isoformat()
        })
        
        # 限制最大数量
        if len(self._accounts) > self._max_history:
            self._accounts = self._accounts[:self._max_history]
        
        self._save()
    
    def add_accounts(self, names: List[str]):
        """批量添加公众号到历史记录
        
        按顺序添加，最后添加的会排在最前面。
        
        Args:
            names: 公众号名称列表
        """
        for name in names:
            self.add_account(name)
    
    def remove_account(self, name: str):
        """从历史记录中删除指定公众号
        
        Args:
            name: 要删除的公众号名称
        """
        self._accounts = [acc for acc in self._accounts if acc['name'] != name]
        self._save()
    
    def clear(self):
        """清空所有历史记录并保存"""
        self._accounts = []
        self._save()
    
    def set_max_history(self, max_count: int):
        """设置最大历史记录数
        
        如果当前记录数超过新的最大值，会自动删除多余的旧记录。
        
        Args:
            max_count: 最大记录数，最小为 1
        """
        self._max_history = max(1, max_count)
        if len(self._accounts) > self._max_history:
            self._accounts = self._accounts[:self._max_history]
            self._save()
    
    def get_max_history(self) -> int:
        """获取当前设置的最大历史记录数"""
        return self._max_history
    
    def contains(self, name: str) -> bool:
        """检查公众号是否在历史记录中
        
        Args:
            name: 公众号名称
            
        Returns:
            True 表示存在，False 表示不存在
        """
        return any(acc['name'] == name for acc in self._accounts)
    
    def get_last_used(self, name: str) -> Optional[str]:
        """获取公众号的最近使用时间
        
        Args:
            name: 公众号名称
            
        Returns:
            ISO 格式的时间字符串（如 "2024-01-01T12:00:00"），
            如果公众号不在历史记录中返回 None
        """
        for acc in self._accounts:
            if acc['name'] == name:
                return acc.get('last_used')
        return None


# 全局单例实例（延迟初始化）
_history_manager: Optional[AccountHistoryManager] = None


def get_history_manager() -> AccountHistoryManager:
    """获取历史记录管理器的全局单例
    
    推荐使用此函数获取管理器实例，而不是直接实例化类。
    
    Returns:
        全局唯一的 AccountHistoryManager 实例
    """
    global _history_manager
    if _history_manager is None:
        _history_manager = AccountHistoryManager()
    return _history_manager