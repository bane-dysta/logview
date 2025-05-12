"""
查看器核心逻辑模块

管理文件查看器的核心状态和逻辑，作为UI和解析器之间的桥梁。
"""

from typing import List, Dict, Optional, Tuple, Any, Callable
import os
from .parser import LogParser
from .highlighter import Highlighter


class ViewerState:
    """查看器状态类，存储查看器的当前状态"""
    def __init__(self):
        self.current_block_index = 0
        self.filtered_indices: List[int] = []
        self.current_filtered_index = 0
        self.filter_mode = False
        self.search_term = ""
        self.top_line = 0  # 当前视图的顶部行号
        self.full_view_mode = False
        self.show_line_numbers = True
        self.highlight_enabled = True
        self.help_mode = False
        self.message = ""
        self.error = False
        self.focus_keyword = False  # 是否聚焦于关键词
        self.focus_offset = 8  # 聚焦关键词时，将关键词放在窗口大约1/3处的位置


class LogViewer:
    """日志查看器核心类，管理查看、导航和搜索功能"""
    
    def __init__(self, filename: Optional[str] = None, separator: Optional[str] = None):
        """
        初始化查看器
        
        Args:
            filename: 要查看的文件路径
            separator: 用于分块的分隔符
        """
        self.parser = LogParser(filename, separator)
        self.highlighter = Highlighter()
        self.state = ViewerState()
        
        # 如果提供了文件名，立即加载并解析
        if filename:
            self.load_file(filename)
    
    def load_file(self, filename: str) -> bool:
        """
        加载并解析文件
        
        Args:
            filename: 文件路径
            
        Returns:
            bool: 是否成功加载文件
        """
        success = self.parser.load_file(filename)
        if success:
            self.parser.parse()
            # 重置状态
            self.reset_state()
            return True
        return False
    
    def reset_state(self):
        """重置查看器状态"""
        self.state.current_block_index = 0
        self.state.filter_mode = False
        self.state.filtered_indices = list(range(len(self.parser.blocks)))
        self.state.current_filtered_index = 0
        self.state.top_line = 0
        self.state.message = f"已加载文件: {os.path.basename(self.parser.filename)}"
        self.state.error = False
        # 保留focus_keyword设置
    
    def reparse_with_separator(self, separator_type: str = "grad", 
                              custom_separator: Optional[str] = None) -> bool:
        """
        使用新的分隔符重新解析文件
        
        Args:
            separator_type: 分隔符类型
            custom_separator: 自定义分隔符
            
        Returns:
            bool: 是否成功重新解析
        """
        if not self.parser.content:
            self.state.message = "没有加载文件"
            self.state.error = True
            return False
            
        self.parser.set_separator(separator_type, custom_separator)
        self.parser.parse()
        self.reset_state()
        self.state.message = f"已使用新分隔符重新解析文件，共 {len(self.parser.blocks)} 个数据块"
        return True
    
    def get_current_block(self) -> Optional[str]:
        """
        获取当前数据块的内容
        
        Returns:
            Optional[str]: 当前数据块内容，如果没有则返回None
        """
        if not self.parser.blocks:
            return None
            
        actual_index = self.get_actual_index()
        return self.parser.get_block(actual_index)
    
    def get_actual_index(self) -> int:
        """
        获取当前块的实际索引
        
        考虑过滤模式和过滤索引
        
        Returns:
            int: 当前块的实际索引
        """
        if self.state.filter_mode and self.state.filtered_indices:
            return self.state.filtered_indices[self.state.current_filtered_index]
        return self.state.current_block_index
    
    def get_block_count(self) -> int:
        """
        获取当前模式下的块数量
        
        Returns:
            int: 可用块的数量
        """
        if self.state.filter_mode and self.state.filtered_indices:
            return len(self.state.filtered_indices)
        return len(self.parser.blocks)
    
    # 导航方法
    def next_block(self) -> bool:
        """
        移动到下一个块
        
        Returns:
            bool: 是否成功导航
        """
        if not self.parser.blocks:
            return False
            
        if self.state.filter_mode and self.state.filtered_indices:
            if self.state.current_filtered_index < len(self.state.filtered_indices) - 1:
                self.state.current_filtered_index += 1
                self.state.current_block_index = self.state.filtered_indices[self.state.current_filtered_index]
                self.state.top_line = 0  # 重置顶部行
                
                # 如果启用了关键词聚焦，自动定位到第一个关键词位置
                if self.state.focus_keyword and self.state.search_term:
                    self._focus_on_keyword()
                    
                return True
        elif not self.state.filter_mode:
            if self.state.current_block_index < len(self.parser.blocks) - 1:
                self.state.current_block_index += 1
                self.state.top_line = 0  # 重置顶部行
                return True
                
        return False
    
    def prev_block(self) -> bool:
        """
        移动到上一个块
        
        Returns:
            bool: 是否成功导航
        """
        if not self.parser.blocks:
            return False
            
        if self.state.filter_mode and self.state.filtered_indices:
            if self.state.current_filtered_index > 0:
                self.state.current_filtered_index -= 1
                self.state.current_block_index = self.state.filtered_indices[self.state.current_filtered_index]
                self.state.top_line = 0  # 重置顶部行
                
                # 如果启用了关键词聚焦，自动定位到第一个关键词位置
                if self.state.focus_keyword and self.state.search_term:
                    self._focus_on_keyword()
                    
                return True
        elif not self.state.filter_mode:
            if self.state.current_block_index > 0:
                self.state.current_block_index -= 1
                self.state.top_line = 0  # 重置顶部行
                return True
                
        return False
    
    def first_block(self) -> bool:
        """
        移动到第一个块
        
        Returns:
            bool: 是否成功导航
        """
        if not self.parser.blocks:
            return False
            
        if self.state.filter_mode and self.state.filtered_indices:
            self.state.current_filtered_index = 0
            self.state.current_block_index = self.state.filtered_indices[0]
        else:
            self.state.current_block_index = 0
            
        self.state.top_line = 0  # 重置顶部行
        
        # 如果启用了关键词聚焦，自动定位到第一个关键词位置
        if self.state.filter_mode and self.state.focus_keyword and self.state.search_term:
            self._focus_on_keyword()
            
        return True
    
    def last_block(self) -> bool:
        """
        移动到最后一个块
        
        Returns:
            bool: 是否成功导航
        """
        if not self.parser.blocks:
            return False
            
        if self.state.filter_mode and self.state.filtered_indices:
            self.state.current_filtered_index = len(self.state.filtered_indices) - 1
            self.state.current_block_index = self.state.filtered_indices[-1]
        else:
            self.state.current_block_index = len(self.parser.blocks) - 1
            
        self.state.top_line = 0  # 重置顶部行
        
        # 如果启用了关键词聚焦，自动定位到第一个关键词位置
        if self.state.filter_mode and self.state.focus_keyword and self.state.search_term:
            self._focus_on_keyword()
            
        return True
    
    def goto_block(self, block_num: int) -> bool:
        """
        跳转到指定块
        
        Args:
            block_num: 要跳转到的块编号（从1开始）
            
        Returns:
            bool: 是否成功跳转
        """
        if not self.parser.blocks or block_num < 1:
            return False
            
        if self.state.filter_mode and self.state.filtered_indices:
            if block_num <= len(self.state.filtered_indices):
                self.state.current_filtered_index = block_num - 1
                self.state.current_block_index = self.state.filtered_indices[self.state.current_filtered_index]
                self.state.top_line = 0  # 重置顶部行
                
                # 如果启用了关键词聚焦，自动定位到第一个关键词位置
                if self.state.focus_keyword and self.state.search_term:
                    self._focus_on_keyword()
                    
                return True
            else:
                self.state.message = f"块编号超出范围 (1-{len(self.state.filtered_indices)})"
                self.state.error = True
                return False
        else:
            if block_num <= len(self.parser.blocks):
                self.state.current_block_index = block_num - 1
                self.state.top_line = 0  # 重置顶部行
                return True
            else:
                self.state.message = f"块编号超出范围 (1-{len(self.parser.blocks)})"
                self.state.error = True
                return False

    def _focus_on_keyword(self) -> bool:
        """
        在当前块中定位到第一个关键词位置，使关键词尽量显示在屏幕中间
        
        Returns:
            bool: 是否找到关键词
        """
        if not self.state.search_term:
            return False
            
        actual_index = self.get_actual_index()
        matches = self.parser.search_in_block(actual_index, self.state.search_term)
        
        if not matches:
            return False
            
        # 定位到第一个匹配行，并考虑偏移量使关键词显示在窗口中间
        matched_line = matches[0][0]
        
        # 计算新的顶部行，使关键词尽量显示在窗口中间
        # 使用focus_offset作为关键词应该在视图中的位置偏移
        new_top_line = max(0, matched_line - self.state.focus_offset)
        
        # 确保不超过文件行数
        block = self.get_current_block()
        if block:
            total_lines = len(block.split('\n'))
            new_top_line = min(new_top_line, max(0, total_lines - 1))
        
        self.state.top_line = new_top_line
        return True
    
    # 搜索方法
    def set_search_term(self, term: str) -> None:
        """
        设置搜索词
        
        Args:
            term: 搜索关键词
        """
        self.state.search_term = term
        self.highlighter.set_search_pattern(term)
    
    def search_next(self) -> bool:
        """
        查找下一个搜索结果
        
        Returns:
            bool: 是否找到
        """
        if not self.state.search_term or not self.parser.blocks:
            return False
            
        # 获取当前块内容并分行
        actual_index = self.get_actual_index()
        block = self.parser.get_block(actual_index)
        if not block:
            return False
            
        lines = block.split('\n')
        
        # 从当前行开始查找
        found = False
        for i in range(self.state.top_line + 1, len(lines)):
            if self.state.search_term.lower() in lines[i].lower():
                self.state.top_line = i
                found = True
                break
        
        if not found:
            # 尝试下一个块
            if self.next_block():
                # 递归调用以在新块中查找
                return self.search_next()
            else:
                self.state.message = "已到达最后一个搜索结果"
                return False
        
        return True
    
    def search_prev(self) -> bool:
        """
        查找上一个搜索结果
        
        Returns:
            bool: 是否找到
        """
        if not self.state.search_term or not self.parser.blocks:
            return False
            
        # 获取当前块内容并分行
        actual_index = self.get_actual_index()
        block = self.parser.get_block(actual_index)
        if not block:
            return False
            
        lines = block.split('\n')
        
        # 从当前行开始向上查找
        found = False
        for i in range(self.state.top_line - 1, -1, -1):
            if self.state.search_term.lower() in lines[i].lower():
                self.state.top_line = i
                found = True
                break
        
        if not found:
            # 尝试上一个块
            if self.prev_block():
                # 先移到最后一行，然后向上搜索
                actual_index = self.get_actual_index()
                block = self.parser.get_block(actual_index)
                if block:
                    lines = block.split('\n')
                    self.state.top_line = len(lines) - 1
                
                # 递归调用以在新块中查找
                return self.search_prev()
            else:
                self.state.message = "已到达第一个搜索结果"
                return False
        
        return True
    
    def filter_blocks(self) -> bool:
        """
        过滤显示包含搜索词的块
        
        Returns:
            bool: 是否找到匹配项
        """
        if not self.state.search_term or not self.parser.blocks:
            return False
            
        self.state.filtered_indices = self.parser.search_blocks(self.state.search_term)
        
        if not self.state.filtered_indices:
            self.state.message = "没有找到匹配的数据块"
            self.state.error = True
            return False
        
        self.state.filter_mode = True
        self.state.current_filtered_index = 0
        self.state.current_block_index = self.state.filtered_indices[0]
        self.state.top_line = 0
        
        # 如果启用了关键词聚焦，自动定位到第一个关键词位置
        if self.state.focus_keyword:
            self._focus_on_keyword()
            
        self.state.message = f"找到 {len(self.state.filtered_indices)} 个匹配的数据块"
        return True
    
    def clear_filter(self) -> None:
        """清除过滤"""
        self.state.filter_mode = False
        self.state.filtered_indices = list(range(len(self.parser.blocks)))
        self.state.message = "已清除过滤"
    
    # 文件操作
    def save_current_block(self, filename: str) -> bool:
        """
        将当前块保存到文件
        
        Args:
            filename: 保存的文件路径
            
        Returns:
            bool: 是否成功保存
        """
        if not self.parser.blocks:
            self.state.message = "没有数据可保存"
            self.state.error = True
            return False
            
        actual_index = self.get_actual_index()
        block = self.parser.get_block(actual_index)
        if not block:
            return False
            
        try:
            with open(filename, 'w', encoding='utf-8') as file:
                file.write(block)
            self.state.message = f"当前数据块已保存到: {filename}"
            return True
        except Exception as e:
            self.state.message = f"保存文件时出错: {str(e)}"
            self.state.error = True
            return False
    
    # 显示选项
    def toggle_full_view(self) -> None:
        """切换完整文件视图和分块视图"""
        self.state.full_view_mode = not self.state.full_view_mode
        self.state.top_line = 0
        
        if self.state.full_view_mode:
            self.state.message = "已切换到完整文件视图"
        else:
            self.state.message = "已切换到分块视图"
    
    def toggle_line_numbers(self) -> None:
        """切换行号显示"""
        self.state.show_line_numbers = not self.state.show_line_numbers
        
        if self.state.show_line_numbers:
            self.state.message = "已启用行号显示"
        else:
            self.state.message = "已禁用行号显示"
    
    def toggle_highlight(self) -> None:
        """切换关键词高亮"""
        self.state.highlight_enabled = not self.state.highlight_enabled
        
        if self.state.highlight_enabled:
            self.state.message = "已启用关键词高亮"
        else:
            self.state.message = "已禁用关键词高亮"
    
    # 滚动控制
    def scroll_up(self, lines: int = 1) -> bool:
        """
        向上滚动指定行数
        
        Args:
            lines: 滚动的行数
            
        Returns:
            bool: 是否成功滚动
        """
        if self.state.top_line >= lines:
            self.state.top_line -= lines
            return True
        elif self.state.top_line > 0:
            self.state.top_line = 0
            return True
        return False
    
    def scroll_down(self, lines: int = 1) -> bool:
        """
        向下滚动指定行数
        
        Args:
            lines: 滚动的行数
            
        Returns:
            bool: 是否成功滚动
        """
        # 获取当前块的总行数
        block = self.get_current_block()
        if not block:
            return False
            
        total_lines = len(block.split('\n'))
        
        if self.state.top_line + lines < total_lines:
            self.state.top_line += lines
            return True
        elif self.state.top_line < total_lines - 1:
            self.state.top_line = total_lines - 1
            return True
        return False
    
    def page_up(self, page_size: int) -> bool:
        """
        向上翻页
        
        Args:
            page_size: 页面大小（行数）
            
        Returns:
            bool: 是否成功翻页
        """
        return self.scroll_up(page_size)
    
    def page_down(self, page_size: int) -> bool:
        """
        向下翻页
        
        Args:
            page_size: 页面大小（行数）
            
        Returns:
            bool: 是否成功翻页
        """
        return self.scroll_down(page_size)
    
    def scroll_to_top(self) -> None:
        """滚动到顶部"""
        self.state.top_line = 0
    
    def scroll_to_bottom(self) -> None:
        """滚动到底部"""
        block = self.get_current_block()
        if block:
            lines = block.split('\n')
            self.state.top_line = max(0, len(lines) - 1)
    
    # 状态控制
    def set_message(self, message: str, error: bool = False) -> None:
        """
        设置状态消息
        
        Args:
            message: 消息内容
            error: 是否为错误消息
        """
        self.state.message = message
        self.state.error = error
    
    def toggle_help_mode(self) -> None:
        """切换帮助模式"""
        self.state.help_mode = not self.state.help_mode
        self.state.top_line = 0 

    def toggle_keyword_focus(self) -> None:
        """切换关键词聚焦功能"""
        self.state.focus_keyword = not self.state.focus_keyword
        
        if self.state.focus_keyword:
            self.state.message = "已启用关键词聚焦 (+ - 调整聚焦位置)"
            # 如果已经在过滤模式并有搜索词，立即聚焦
            if self.state.filter_mode and self.state.search_term:
                self._focus_on_keyword()
        else:
            self.state.message = "已禁用关键词聚焦"
    
    def increase_focus_offset(self) -> None:
        """增加聚焦关键词的偏移量（使关键词显示位置更靠上）"""
        # 最大偏移量限制为30行，避免过度偏移
        if self.state.focus_offset < 30:
            self.state.focus_offset += 1
            self.state.message = f"聚焦偏移量: {self.state.focus_offset}行"
            
            # 如果当前处于聚焦模式，立即应用新的偏移量
            if self.state.focus_keyword and self.state.filter_mode and self.state.search_term:
                self._focus_on_keyword()
    
    def decrease_focus_offset(self) -> None:
        """减少聚焦关键词的偏移量（使关键词显示位置更靠下）"""
        # 最小偏移量为1，保证至少有一行上下文
        if self.state.focus_offset > 1:
            self.state.focus_offset -= 1
            self.state.message = f"聚焦偏移量: {self.state.focus_offset}行"
            
            # 如果当前处于聚焦模式，立即应用新的偏移量
            if self.state.focus_keyword and self.state.filter_mode and self.state.search_term:
                self._focus_on_keyword() 