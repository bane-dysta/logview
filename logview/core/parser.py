"""
文件解析模块

提供对日志文件的读取、分块和初步处理功能。
"""

import re
import os
from typing import List, Dict, Optional, Tuple
from ..utils.config import load_separators, DEFAULT_SEPARATORS


class LogParser:
    """日志文件解析器，支持基于分隔符的分块功能"""
    
    def __init__(self, filename: Optional[str] = None, separator: Optional[str] = None):
        """
        初始化解析器
        
        Args:
            filename: 文件路径
            separator: 块分隔符，默认使用Grad分隔符
        """
        self.filename = filename
        self.content = ""
        self.blocks: List[str] = []
        
        # 加载分隔符配置
        self.separators = load_separators()
        
        # 设置分隔符
        if separator:
            self.separator = separator
        else:
            self.separator = self.separators.get("grad", DEFAULT_SEPARATORS["grad"])
    
    def set_separator(self, separator_type: str = "grad", custom_separator: Optional[str] = None) -> None:
        """
        设置分隔符
        
        Args:
            separator_type: 分隔符类型，可以是'grad', 'irc', 'custom'
            custom_separator: 自定义分隔符，当separator_type为'custom'时使用
        """
        if separator_type == "custom" and custom_separator:
            self.separator = custom_separator
        elif separator_type in self.separators:
            self.separator = self.separators[separator_type]
        else:
            # 默认使用Grad分隔符
            self.separator = self.separators.get("grad", DEFAULT_SEPARATORS["grad"])
    
    def load_file(self, filename: Optional[str] = None) -> bool:
        """
        加载文件内容
        
        Args:
            filename: 文件路径，如不提供则使用初始化时设置的文件路径
            
        Returns:
            bool: 加载是否成功
        """
        if filename:
            self.filename = filename
            
        if not self.filename or not os.path.exists(self.filename):
            return False
            
        try:
            with open(self.filename, 'r', encoding='utf-8', errors='ignore') as file:
                self.content = file.read()
            return True
        except Exception:
            return False
    
    def parse(self) -> List[str]:
        """
        根据分隔符解析文件内容为块
        
        Returns:
            List[str]: 分块后的内容列表
        """
        if not self.content:
            return []
            
        # 使用正则表达式分割文件
        pattern = re.escape(self.separator)
        parts = re.split(f"({pattern})", self.content)
        
        # 将分隔符与内容合并（除了第一块可能没有前导分隔符）
        self.blocks = []
        for i in range(0, len(parts), 2):
            # 如果还有下一个分隔符，则将其添加到当前块
            if i+1 < len(parts):
                self.blocks.append(parts[i] + parts[i+1])
            else:
                self.blocks.append(parts[i])
        
        # 如果文件不包含分隔符，则将整个文件作为一个块
        if not self.blocks:
            self.blocks = [self.content]
            
        return self.blocks
        
    def get_block(self, index: int) -> Optional[str]:
        """
        获取指定索引的块
        
        Args:
            index: 块索引
            
        Returns:
            Optional[str]: 指定索引的块内容，如果索引无效则返回None
        """
        if 0 <= index < len(self.blocks):
            return self.blocks[index]
        return None
    
    def search_blocks(self, keyword: str) -> List[int]:
        """
        搜索包含关键词的块，返回匹配的块索引列表
        
        Args:
            keyword: 要搜索的关键词
            
        Returns:
            List[int]: 匹配块的索引列表
        """
        if not keyword or not self.blocks:
            return []
            
        return [i for i, block in enumerate(self.blocks) 
                if keyword.lower() in block.lower()]
    
    def search_in_block(self, block_index: int, keyword: str) -> List[Tuple[int, str]]:
        """
        在指定块内搜索关键词，返回匹配的行号和内容
        
        Args:
            block_index: 块索引
            keyword: 要搜索的关键词
            
        Returns:
            List[Tuple[int, str]]: 匹配行的行号和内容列表
        """
        if not keyword or block_index < 0 or block_index >= len(self.blocks):
            return []
            
        block = self.blocks[block_index]
        lines = block.split('\n')
        
        return [(i, line) for i, line in enumerate(lines)
                if keyword.lower() in line.lower()] 