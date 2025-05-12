"""
配置文件管理实用工具

提供配置文件的读写功能，包括关键词和分隔符配置。
"""

import os
import json
from typing import Dict, List, Any, Optional


# 默认配置目录
CONFIG_DIR = os.path.expanduser("~/.config/logview")

# 默认配置文件
KEYWORDS_FILE = os.path.join(CONFIG_DIR, "keywords.json")
SEPARATORS_FILE = os.path.join(CONFIG_DIR, "separators.json")
KEYWORD_TYPES_FILE = os.path.join(CONFIG_DIR, "keyword_types.json")

# 默认分隔符
DEFAULT_SEPARATORS = {
    "grad": "GradGradGradGradGradGradGradGradGradGradGradGradGradGradGradGradGradGrad",
    "irc": "IRC-IRC-IRC-IRC-IRC-IRC-IRC-IRC-IRC-IRC-IRC-IRC-IRC-IRC-IRC-IRC-IRC-IRC",
    "custom": ""
}

# 默认关键词类型
DEFAULT_KEYWORD_TYPES = {
    "common": [
        "SCF Done", "Excited State   1", "Optimization completed", "normal coordinates",
        "Orbital symmetries", "Mulliken charges", "APT charges:", "Converged?", 
        "Standard orientation", "Input orientation", "Frequency", "Failed", 
        "dipole moments", "Point Number:"
    ],
    "error": ["Error", "Failed", "错误", "失败"],
    "warning": ["Warning", "警告"],
    "success": ["SCF Done", "Optimization completed", "Converged"]
}


def ensure_config_dir():
    """确保配置目录存在"""
    if not os.path.exists(CONFIG_DIR):
        try:
            os.makedirs(CONFIG_DIR, exist_ok=True)
            return True
        except Exception as e:
            print(f"创建配置目录失败: {e}")
            return False
    return True


def load_keywords() -> List[str]:
    """
    加载用户自定义关键词列表
    
    Returns:
        List[str]: 关键词列表
    """
    # 确保配置目录存在
    if not ensure_config_dir():
        return []
    
    # 如果配置文件不存在，返回空列表
    if not os.path.exists(KEYWORDS_FILE):
        return []
    
    # 读取配置文件
    try:
        with open(KEYWORDS_FILE, 'r', encoding='utf-8') as f:
            keywords = json.load(f)
            if isinstance(keywords, list):
                return [k for k in keywords if isinstance(k, str)]
            else:
                return []
    except Exception as e:
        print(f"读取关键词配置失败: {e}")
        return []


def save_keywords(keywords: List[str]) -> bool:
    """
    保存用户自定义关键词列表
    
    Args:
        keywords: 要保存的关键词列表
        
    Returns:
        bool: 是否成功保存
    """
    # 确保配置目录存在
    if not ensure_config_dir():
        return False
    
    # 保存配置文件
    try:
        with open(KEYWORDS_FILE, 'w', encoding='utf-8') as f:
            json.dump(keywords, f, indent=2)
        return True
    except Exception as e:
        print(f"保存关键词配置失败: {e}")
        return False


def load_keyword_types() -> Dict[str, List[str]]:
    """
    加载关键词类型配置
    
    Returns:
        Dict[str, List[str]]: 关键词类型配置字典
    """
    # 确保配置目录存在
    if not ensure_config_dir():
        return DEFAULT_KEYWORD_TYPES.copy()
    
    # 如果配置文件不存在，创建默认配置文件
    if not os.path.exists(KEYWORD_TYPES_FILE):
        if not save_keyword_types(DEFAULT_KEYWORD_TYPES):
            return DEFAULT_KEYWORD_TYPES.copy()
    
    # 读取配置文件
    try:
        with open(KEYWORD_TYPES_FILE, 'r', encoding='utf-8') as f:
            keyword_types = json.load(f)
            if isinstance(keyword_types, dict):
                return keyword_types
            else:
                return DEFAULT_KEYWORD_TYPES.copy()
    except Exception as e:
        print(f"读取关键词类型配置失败: {e}")
        return DEFAULT_KEYWORD_TYPES.copy()


def save_keyword_types(keyword_types: Dict[str, List[str]]) -> bool:
    """
    保存关键词类型配置
    
    Args:
        keyword_types: 要保存的关键词类型配置
        
    Returns:
        bool: 是否成功保存
    """
    # 确保配置目录存在
    if not ensure_config_dir():
        return False
    
    # 保存配置文件
    try:
        with open(KEYWORD_TYPES_FILE, 'w', encoding='utf-8') as f:
            json.dump(keyword_types, f, indent=2)
        return True
    except Exception as e:
        print(f"保存关键词类型配置失败: {e}")
        return False


def load_separators() -> Dict[str, str]:
    """
    加载分隔符配置
    
    Returns:
        Dict[str, str]: 分隔符配置字典
    """
    # 确保配置目录存在
    if not ensure_config_dir():
        return DEFAULT_SEPARATORS.copy()
    
    # 如果配置文件不存在，创建默认配置文件
    if not os.path.exists(SEPARATORS_FILE):
        if not save_separators(DEFAULT_SEPARATORS):
            return DEFAULT_SEPARATORS.copy()
    
    # 读取配置文件
    try:
        with open(SEPARATORS_FILE, 'r', encoding='utf-8') as f:
            separators = json.load(f)
            if isinstance(separators, dict):
                return separators
            else:
                return DEFAULT_SEPARATORS.copy()
    except Exception as e:
        print(f"读取分隔符配置失败: {e}")
        return DEFAULT_SEPARATORS.copy()


def save_separators(separators: Dict[str, str]) -> bool:
    """
    保存分隔符配置
    
    Args:
        separators: 要保存的分隔符配置
        
    Returns:
        bool: 是否成功保存
    """
    # 确保配置目录存在
    if not ensure_config_dir():
        return False
    
    # 保存配置文件
    try:
        with open(SEPARATORS_FILE, 'w', encoding='utf-8') as f:
            json.dump(separators, f, indent=2)
        return True
    except Exception as e:
        print(f"保存分隔符配置失败: {e}")
        return False 