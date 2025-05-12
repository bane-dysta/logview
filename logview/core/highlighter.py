"""
文本高亮模块

提供对日志文件文本的高亮处理功能。
"""

from typing import List, Dict, Tuple, Optional, Any
import re


class HighlightPattern:
    """高亮模式类，定义要高亮的关键词和高亮样式"""
    
    def __init__(self, pattern: str, style: Dict[str, Any], whole_line: bool = False, 
                 is_regex: bool = False, case_sensitive: bool = False):
        """
        初始化高亮模式
        
        Args:
            pattern: 要高亮的文本模式
            style: 高亮样式，用于渲染器
            whole_line: 是否高亮整行
            is_regex: pattern是否为正则表达式
            case_sensitive: 是否区分大小写
        """
        self.pattern = pattern
        self.style = style
        self.whole_line = whole_line
        self.is_regex = is_regex
        self.case_sensitive = case_sensitive
        
        # 预编译正则表达式
        if is_regex:
            flags = 0 if case_sensitive else re.IGNORECASE
            try:
                self.regex = re.compile(pattern, flags)
            except re.error:
                # 如果正则表达式无效，退回到普通文本匹配
                self.is_regex = False
                self.regex = None
        else:
            self.regex = None


class Highlighter:
    """文本高亮器，支持关键词、正则表达式和主题配置"""
    
    # 默认高亮类型和样式
    DEFAULT_STYLES = {
        "keyword": {"color": "cyan", "attrs": []},
        "error": {"color": "red", "attrs": ["bold"]},
        "warning": {"color": "yellow", "attrs": []},
        "success": {"color": "green", "attrs": []},
        "search": {"color": "black", "bgcolor": "yellow", "attrs": []},
    }
    
    # 常见的量子化学关键词
    COMMON_KEYWORDS = [
        "SCF Done", "Excited State   1", "Optimization completed", "normal coordinates",
        "Orbital symmetries", "Mulliken charges", "APT charges:", "Converged?", 
        "Standard orientation", "Input orientation", "Frequency", "Failed", 
        "dipole moments", "Point Number:"
    ]
    
    def __init__(self):
        """初始化高亮器"""
        self.patterns: List[HighlightPattern] = []
        self.search_pattern: Optional[HighlightPattern] = None
        self.enabled = True
        
        # 初始化默认高亮模式
        self._setup_default_patterns()
    
    def _setup_default_patterns(self):
        """设置默认的高亮模式"""
        # 错误关键词
        for keyword in ["Error", "Failed", "错误", "失败"]:
            self.add_pattern(
                keyword, 
                self.DEFAULT_STYLES["error"],
                whole_line=True,
                case_sensitive=False
            )
        
        # 警告关键词
        for keyword in ["Warning", "警告"]:
            self.add_pattern(
                keyword, 
                self.DEFAULT_STYLES["warning"],
                whole_line=True,
                case_sensitive=False
            )
        
        # 成功关键词
        for keyword in ["SCF Done", "Optimization completed", "Converged"]:
            self.add_pattern(
                keyword, 
                self.DEFAULT_STYLES["success"],
                whole_line=True,
                case_sensitive=False
            )
        
        # 常见的量子化学关键词
        for keyword in self.COMMON_KEYWORDS:
            self.add_pattern(
                keyword, 
                self.DEFAULT_STYLES["keyword"],
                whole_line=False,
                case_sensitive=False
            )
    
    def add_pattern(self, pattern: str, style: Dict[str, Any], whole_line: bool = False, 
                   is_regex: bool = False, case_sensitive: bool = False) -> None:
        """
        添加高亮模式
        
        Args:
            pattern: 要高亮的文本模式
            style: 高亮样式
            whole_line: 是否高亮整行
            is_regex: pattern是否为正则表达式
            case_sensitive: 是否区分大小写
        """
        self.patterns.append(
            HighlightPattern(pattern, style, whole_line, is_regex, case_sensitive)
        )
    
    def clear_patterns(self):
        """清除所有高亮模式"""
        self.patterns = []
    
    def reset_to_defaults(self):
        """重置为默认高亮模式"""
        self.clear_patterns()
        self._setup_default_patterns()
    
    def set_search_pattern(self, pattern: str, case_sensitive: bool = False):
        """
        设置当前的搜索高亮模式
        
        Args:
            pattern: 搜索关键词
            case_sensitive: 是否区分大小写
        """
        if not pattern:
            self.search_pattern = None
            return
            
        self.search_pattern = HighlightPattern(
            pattern,
            self.DEFAULT_STYLES["search"],
            whole_line=False,
            is_regex=False,
            case_sensitive=case_sensitive
        )
    
    def find_matches(self, text: str, pattern: HighlightPattern) -> List[Tuple[int, int]]:
        """
        查找文本中匹配的位置
        
        Args:
            text: 要检查的文本
            pattern: 高亮模式
            
        Returns:
            List[Tuple[int, int]]: 匹配的起始和结束位置列表
        """
        matches = []
        
        if pattern.is_regex and pattern.regex:
            for match in pattern.regex.finditer(text):
                matches.append((match.start(), match.end()))
        else:
            search_text = pattern.pattern
            target_text = text
            
            if not pattern.case_sensitive:
                search_text = search_text.lower()
                target_text = text.lower()
                
            start = 0
            while True:
                start = target_text.find(search_text, start)
                if start == -1:
                    break
                matches.append((start, start + len(search_text)))
                start += 1
                
        return matches 