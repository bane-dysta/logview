"""
基于curses的终端用户界面实现

提供VIM风格的命令行界面，支持块导航、搜索和高亮显示等功能。
"""

import curses
import os
import sys
from typing import Dict, List, Optional, Tuple, Any, Callable
from ..core.viewer import LogViewer


class CursesUI:
    """基于curses的终端用户界面"""
    
    def __init__(self, viewer: LogViewer):
        """
        初始化UI
        
        Args:
            viewer: LogViewer实例
        """
        self.viewer = viewer
        self.stdscr = None
        self.height = 0
        self.width = 0
        self.status_win = None
        self.text_win = None
        self.command_win = None
        self.message_win = None
        
        # 命令模式状态
        self.command_mode = False
        self.command_buffer = ""
        
        # 注册命令处理器
        self.commands = self._setup_commands()
    
    def _setup_commands(self) -> Dict[str, Callable]:
        """
        设置命令映射
        
        Returns:
            Dict[str, Callable]: 命令名称到处理函数的映射
        """
        return {
            'q': self.quit,
            'h': self.toggle_help,
            'n': self.next_block,
            'p': self.prev_block,
            'f': self.first_block,
            'l': self.last_block,
            '/': self.start_search,
            '?': self.start_search_backward,
            'N': self.next_search_result,
            'P': self.prev_search_result,
            's': self.start_save,
            'g': self.start_goto,
            'k': self.scroll_up,
            'j': self.scroll_down,
            'K': self.scroll_up_page,
            'J': self.scroll_down_page,
            'v': self.toggle_full_view,
            '#': self.toggle_line_numbers,
            'H': self.toggle_highlight,
            'F': self.filter_blocks,
            'c': self.clear_filter,
            'O': self.toggle_keyword_focus,
            '+': self.increase_focus_offset,
            '-': self.decrease_focus_offset
        }
    
    def start(self):
        """启动UI"""
        curses.wrapper(self._main)
    
    def _main(self, stdscr):
        """主函数，由curses.wrapper调用"""
        self.stdscr = stdscr
        self._setup_curses()
        self._setup_windows()
        self._main_loop()
    
    def _setup_curses(self):
        """设置curses环境"""
        # 隐藏光标
        curses.curs_set(0)
        
        # 使用标准终端的颜色
        curses.start_color()
        curses.use_default_colors()
        
        # 颜色配对设置
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)  # 状态栏
        curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_YELLOW)  # 搜索高亮
        curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_GREEN)  # 命令栏
        curses.init_pair(4, curses.COLOR_RED, -1)  # 错误关键词
        curses.init_pair(5, curses.COLOR_YELLOW, -1)  # 警告关键词
        curses.init_pair(6, curses.COLOR_GREEN, -1)  # 成功关键词
        curses.init_pair(7, curses.COLOR_CYAN, -1)  # 关键词高亮
        curses.init_pair(8, curses.COLOR_WHITE, curses.COLOR_RED)  # 错误信息
        
        # 获取终端的高度和宽度
        self.height, self.width = self.stdscr.getmaxyx()
    
    def _setup_windows(self):
        """创建窗口"""
        self.height, self.width = self.stdscr.getmaxyx()
        
        # 状态栏: 1行，在顶部
        self.status_win = curses.newwin(1, self.width, 0, 0)
        
        # 文本显示区域: 高度-3行，在状态栏下方
        self.text_win = curses.newwin(self.height - 3, self.width, 1, 0)
        
        # 命令栏: 1行，在底部
        self.command_win = curses.newwin(1, self.width, self.height - 2, 0)
        
        # 消息栏: 1行，在命令栏下方
        self.message_win = curses.newwin(1, self.width, self.height - 1, 0)
        
        # 启用按键功能
        self.stdscr.keypad(True)
        self.text_win.keypad(True)
        self.command_win.keypad(True)
        
        # 启用即时输入
        self.stdscr.nodelay(False)
        
        # 计算并更新Viewer的聚焦偏移量，使关键词显示在窗口中间
        text_height = self.height - 3  # 文本窗口的高度
        # 设置偏移量为文本区域高度的1/3左右，这样关键词会在视图的上部1/3处
        self.viewer.state.focus_offset = max(1, text_height // 3)
    
    def _resize_windows(self):
        """处理窗口大小变化"""
        self.stdscr.clear()
        self._setup_windows()
        self.display()
    
    def display(self):
        """显示当前内容"""
        self.draw_status_bar()
        self.draw_text_content()
        if self.command_mode:
            self.draw_command_bar()
        self.draw_message_bar()
    
    def draw_status_bar(self):
        """绘制状态栏"""
        self.status_win.clear()
        self.status_win.bkgd(' ', curses.color_pair(1))
        
        # 显示文件名和块信息
        file_info = f" {os.path.basename(self.viewer.parser.filename) if self.viewer.parser.filename else '无文件'}"
        
        # 显示当前块信息
        if self.viewer.parser.blocks:
            if self.viewer.state.filter_mode:
                block_info = f"[过滤块 {self.viewer.state.current_filtered_index+1}/{len(self.viewer.state.filtered_indices)}]"
                block_info += f" [原始块 {self.viewer.get_actual_index()+1}/{len(self.viewer.parser.blocks)}]"
            else:
                block_info = f"[块 {self.viewer.state.current_block_index+1}/{len(self.viewer.parser.blocks)}]"
        else:
            block_info = "[无数据]"
        
        mode_info = []
        if self.viewer.state.full_view_mode:
            mode_info.append("完整视图")
        if self.viewer.state.filter_mode:
            mode_info.append("过滤模式")
        if self.viewer.state.highlight_enabled:
            mode_info.append("关键词高亮")
        if self.viewer.state.focus_keyword:
            mode_info.append("聚焦关键词")
        if self.viewer.state.help_mode:
            mode_info.append("帮助模式")
            
        mode_str = " ".join(mode_info)
        
        # 组合状态信息
        status_str = f"{file_info} {block_info} {mode_str}"
        
        # 确保状态信息不超过窗口宽度
        status_str = status_str[:self.width - 1]
        
        self.status_win.addstr(0, 0, status_str)
        self.status_win.refresh()
    
    def draw_text_content(self):
        """绘制文本内容区域"""
        self.text_win.clear()
        
        # 没有数据时的提示
        if not self.viewer.parser.blocks:
            self.text_win.addstr(0, 0, "没有数据可显示 (按 'h' 获取帮助)")
            self.text_win.refresh()
            return
        
        # 帮助模式
        if self.viewer.state.help_mode:
            self.draw_help()
            return
        
        # 获取当前块内容
        block = self.viewer.get_current_block()
        if not block:
            return
            
        # 完整视图模式
        if self.viewer.state.full_view_mode:
            self.draw_full_view()
            return
        
        # 分块视图模式
        self.draw_block_view(block)
    
    def draw_block_view(self, content: str):
        """
        绘制分块视图
        
        Args:
            content: 要显示的文本内容
        """
        # 将内容分割成行
        lines = content.split('\n')
        
        # 获取可显示的行数
        visible_height = self.height - 3  # 减去状态栏和命令栏
        
        # 确保top_line不超过总行数
        if self.viewer.state.top_line >= len(lines):
            self.viewer.state.top_line = max(0, len(lines) - 1)
        
        # 获取当前视图中应该显示的行
        start_line = self.viewer.state.top_line
        end_line = min(start_line + visible_height, len(lines))
        display_lines = lines[start_line:end_line]
        
        # 绘制行号和内容
        for i, line in enumerate(display_lines):
            # 当前行的实际行号
            actual_line_num = start_line + i
            
            # 显示行号
            if self.viewer.state.show_line_numbers:
                line_num_str = f"{actual_line_num + 1:4} "
                self.text_win.addstr(i, 0, line_num_str)
                line_start_pos = 5
            else:
                line_start_pos = 0
            
            # 处理行的宽度
            line_width = self.width - line_start_pos
            if len(line) > line_width:
                line = line[:line_width - 3] + "..."
            
            # 绘制行内容
            try:
                self.text_win.addstr(i, line_start_pos, line)
                
                # 高亮关键词
                if self.viewer.state.highlight_enabled:
                    self.highlight_line(i, line, line_start_pos)
                
                # 高亮搜索词
                if self.viewer.state.search_term:
                    self.highlight_search(i, line, line_start_pos)
            except curses.error:
                # 忽略超出界限的绘制错误
                pass
        
        self.text_win.refresh()
    
    def draw_full_view(self):
        """绘制完整文件视图"""
        # 如果需要完整实现，可以考虑将所有块连接起来显示
        self.text_win.addstr(0, 0, "完整文件视图模式 (尚未完全实现)")
        self.text_win.addstr(1, 0, "请使用分块视图模式进行查看")
        self.text_win.refresh()
    
    def highlight_line(self, line_num: int, line_text: str, start_pos: int):
        """
        高亮一行文本中的关键词
        
        Args:
            line_num: 屏幕上的行号
            line_text: 行文本内容
            start_pos: 开始绘制的位置
        """
        line_text_lower = line_text.lower()
        
        # 检查各种关键词类型并高亮
        # 错误关键词
        for keyword in ["error", "failed", "错误", "失败"]:
            if keyword.lower() in line_text_lower:
                try:
                    self.text_win.addstr(line_num, start_pos, line_text, curses.color_pair(4))
                    return  # 整行高亮后返回
                except curses.error:
                    pass
        
        # 警告关键词
        for keyword in ["warning", "警告"]:
            if keyword.lower() in line_text_lower:
                try:
                    self.text_win.addstr(line_num, start_pos, line_text, curses.color_pair(5))
                    return  # 整行高亮后返回
                except curses.error:
                    pass
        
        # 成功关键词
        for keyword in ["scf done", "optimization completed", "converged"]:
            if keyword.lower() in line_text_lower:
                try:
                    self.text_win.addstr(line_num, start_pos, line_text, curses.color_pair(6))
                    return  # 整行高亮后返回
                except curses.error:
                    pass
        
        # 其他关键词
        for keyword in self.viewer.highlighter.COMMON_KEYWORDS:
            keyword_lower = keyword.lower()
            if keyword_lower in line_text_lower:
                start_idx = line_text_lower.find(keyword_lower)
                end_idx = start_idx + len(keyword)
                try:
                    # 高亮前面部分
                    self.text_win.addstr(line_num, start_pos, line_text[:start_idx])
                    # 高亮关键词
                    self.text_win.addstr(line_num, start_pos + start_idx, line_text[start_idx:end_idx], curses.color_pair(7))
                    # 高亮后面部分
                    self.text_win.addstr(line_num, start_pos + end_idx, line_text[end_idx:])
                except curses.error:
                    pass
                return  # 只处理第一个匹配的关键词
    
    def highlight_search(self, line_num: int, line_text: str, start_pos: int):
        """
        高亮搜索词
        
        Args:
            line_num: 屏幕上的行号
            line_text: 行文本内容
            start_pos: 开始绘制的位置
        """
        if not self.viewer.state.search_term:
            return
            
        term_lower = self.viewer.state.search_term.lower()
        line_lower = line_text.lower()
        
        # 找到所有匹配项
        start_idx = 0
        while start_idx < len(line_lower):
            idx = line_lower.find(term_lower, start_idx)
            if idx == -1:
                break
                
            end_idx = idx + len(self.viewer.state.search_term)
            try:
                self.text_win.addstr(line_num, start_pos + idx, line_text[idx:end_idx], curses.color_pair(2))
            except curses.error:
                pass
                
            start_idx = end_idx
    
    def draw_command_bar(self):
        """绘制命令栏"""
        self.command_win.clear()
        self.command_win.bkgd(' ', curses.color_pair(3))
        
        # 显示命令输入
        if len(self.command_buffer) > self.width - 1:
            # 如果命令太长，只显示最后部分
            display_cmd = self.command_buffer[-(self.width - 1):]
        else:
            display_cmd = self.command_buffer
            
        self.command_win.addstr(0, 0, display_cmd)
        self.command_win.refresh()
    
    def draw_message_bar(self):
        """绘制消息栏"""
        self.message_win.clear()
        
        if self.viewer.state.error:
            self.message_win.bkgd(' ', curses.color_pair(8))
        else:
            self.message_win.bkgd(' ', curses.color_pair(3))
        
        # 确保消息不超过窗口宽度
        message = self.viewer.state.message
        if len(message) > self.width - 1:
            message = message[:self.width - 4] + "..."
            
        self.message_win.addstr(0, 0, message)
        self.message_win.refresh()
    
    def draw_help(self):
        """绘制帮助信息"""
        help_text = [
            "量子化学输出文件命令行查看器 - 帮助",
            "=============================================",
            "导航命令:",
            "  n / 右箭头 - 下一个块",
            "  p / 左箭头 - 上一个块",
            "  f - 第一个块",
            "  l - 最后一个块",
            "  g - 跳转到指定块 (例如: g10)",
            "  j / 下箭头 - 向下滚动",
            "  k / 上箭头 - 向上滚动",
            "  J / PageDown - 向下翻页",
            "  K / PageUp - 向上翻页",
            "",
            "搜索和过滤:",
            "  / - 开始搜索",
            "  ? - 开始向后搜索",
            "  N - 下一个搜索结果",
            "  P - 上一个搜索结果",
            "  F - 过滤模式 (只显示包含搜索词的块)",
            "  O - 切换关键词聚焦 (过滤模式下自动聚焦关键词)",
            "  + - 增加关键词聚焦偏移量 (关键词位置上移)",
            "  - - 减少关键词聚焦偏移量 (关键词位置下移)",
            "  c - 清除过滤",
            "",
            "显示选项:",
            "  v - 切换完整文件视图/分块视图",
            "  # - 切换行号显示",
            "  H - 切换关键词高亮",
            "",
            "文件操作:",
            "  s - 保存当前块到文件",
            "  q - 退出程序",
            "",
            "按任意键返回..."
        ]
        
        # 获取可显示的行数
        visible_height = self.height - 3
        
        # 确保top_line不超过帮助文本的总行数
        if self.viewer.state.top_line >= len(help_text):
            self.viewer.state.top_line = max(0, len(help_text) - 1)
        
        # 获取当前视图中应该显示的行
        start_line = self.viewer.state.top_line
        end_line = min(start_line + visible_height, len(help_text))
        display_lines = help_text[start_line:end_line]
        
        # 绘制帮助内容
        for i, line in enumerate(display_lines):
            try:
                self.text_win.addstr(i, 0, line)
            except curses.error:
                pass
        
        self.text_win.refresh()
    
    def _process_command_input(self):
        """处理命令输入"""
        command_complete = False
        curses.curs_set(1)  # 显示光标
        
        while not command_complete:
            self.draw_command_bar()
            key = self.command_win.getch()
            
            if key == ord('\n'):  # Enter键
                command_complete = True
                self.execute_command()
            elif key == 27:  # Escape键
                command_complete = True
                self.command_mode = False
                self.display()
            elif key == curses.KEY_BACKSPACE or key == 127:  # Backspace键
                if len(self.command_buffer) > 1:  # 保留命令前缀
                    self.command_buffer = self.command_buffer[:-1]
                else:
                    command_complete = True
                    self.command_mode = False
                    self.display()
            elif key == curses.KEY_RESIZE:
                self._resize_windows()
            elif 32 <= key <= 126:  # 可打印字符
                self.command_buffer += chr(key)
        
        curses.curs_set(0)  # 隐藏光标
    
    def execute_command(self):
        """执行命令"""
        if not self.command_buffer:
            self.command_mode = False
            self.display()
            return
        
        # 搜索命令
        if self.command_buffer.startswith('/'):
            search_term = self.command_buffer[1:]
            if search_term:
                self.viewer.set_search_term(search_term)
                self.viewer.set_message(f"搜索: {search_term}")
                # 跳转到第一个匹配项
                self.viewer.state.top_line = 0  # 重置顶部行
                self.viewer.search_next()
            else:
                self.viewer.set_message("请输入搜索关键词", True)
        
        # 向后搜索命令
        elif self.command_buffer.startswith('?'):
            search_term = self.command_buffer[1:]
            if search_term:
                self.viewer.set_search_term(search_term)
                self.viewer.set_message(f"向后搜索: {search_term}")
                # 跳转到最后一个匹配项
                block = self.viewer.get_current_block()
                if block:
                    lines = block.split('\n')
                    self.viewer.state.top_line = len(lines) - 1
                self.viewer.search_prev()
            else:
                self.viewer.set_message("请输入搜索关键词", True)
        
        # 跳转命令
        elif self.command_buffer.startswith('g'):
            block_num = self.command_buffer[1:].strip()
            if block_num.isdigit():
                if self.viewer.goto_block(int(block_num)):
                    self.viewer.set_message(f"已跳转到块 {block_num}")
            else:
                self.viewer.set_message("请输入有效的块编号", True)
        
        # 保存命令
        elif self.command_buffer.startswith('s '):
            filename = self.command_buffer[2:].strip()
            if filename:
                self.viewer.save_current_block(filename)
            else:
                self.viewer.set_message("请输入文件名", True)
        
        # 其他命令
        else:
            self.viewer.set_message(f"未知命令: {self.command_buffer}", True)
        
        self.command_mode = False
        self.display()
    
    def _main_loop(self):
        """主循环，处理用户输入"""
        self.display()
        
        while True:
            key = self.stdscr.getch()
            
            if key == curses.KEY_RESIZE:
                self._resize_windows()
            elif key == ord(':'):  # 进入命令模式
                self.command_mode = True
                self.command_buffer = ":"
                self.draw_command_bar()
                self._process_command_input()
            elif self.viewer.state.help_mode:  # 在帮助模式下，任意键返回
                if key == ord('j'):  # 在帮助模式下仍然允许j键向下滚动
                    self.viewer.scroll_down()
                    self.display()
                elif key == ord('k'):  # 允许k键向上滚动
                    self.viewer.scroll_up()
                    self.display()
                elif key == ord('J'):  # 允许J键翻页
                    self.viewer.page_down(self.height - 3)
                    self.display()
                elif key == ord('K'):  # 允许K键翻页
                    self.viewer.page_up(self.height - 3)
                    self.display()
                else:
                    self.viewer.toggle_help_mode()  # 其他键退出帮助模式
                    self.display()
            elif 0 < key < 256 and chr(key) in self.commands:  # 执行快捷键命令
                self.commands[chr(key)]()
                self.display()
            elif key == curses.KEY_UP:  # 上方向键
                self.viewer.scroll_up()
                self.display()
            elif key == curses.KEY_DOWN:  # 下方向键
                self.viewer.scroll_down()
                self.display()
            elif key == curses.KEY_LEFT:  # 左方向键 - 映射到上一个块
                self.prev_block()
                self.display()
            elif key == curses.KEY_RIGHT:  # 右方向键 - 映射到下一个块
                self.next_block()
                self.display()
            elif key == curses.KEY_NPAGE:  # Page Down
                self.viewer.page_down(self.height - 3)
                self.display()
            elif key == curses.KEY_PPAGE:  # Page Up
                self.viewer.page_up(self.height - 3)
                self.display()
            elif key == curses.KEY_HOME:  # Home
                self.viewer.scroll_to_top()
                self.display()
            elif key == curses.KEY_END:  # End
                self.viewer.scroll_to_bottom()
                self.display()
            elif key == 27:  # Escape键
                # 如果在过滤模式下，清除过滤
                if self.viewer.state.filter_mode:
                    self.viewer.clear_filter()
                    self.display()
                # 如果有搜索词，清除搜索
                elif self.viewer.state.search_term:
                    self.viewer.set_search_term("")
                    self.viewer.set_message("已清除搜索")
                    self.display()
    
    # 命令处理函数
    def quit(self):
        """退出程序"""
        sys.exit(0)
    
    def toggle_help(self):
        """切换帮助模式"""
        self.viewer.toggle_help_mode()
    
    def next_block(self):
        """下一个块"""
        if self.viewer.next_block():
            self.viewer.set_message("已移动到下一个块")
        else:
            self.viewer.set_message("已到达最后一个块")
    
    def prev_block(self):
        """上一个块"""
        if self.viewer.prev_block():
            self.viewer.set_message("已移动到上一个块")
        else:
            self.viewer.set_message("已到达第一个块")
    
    def first_block(self):
        """第一个块"""
        if self.viewer.first_block():
            self.viewer.set_message("已移动到第一个块")
    
    def last_block(self):
        """最后一个块"""
        if self.viewer.last_block():
            self.viewer.set_message("已移动到最后一个块")
    
    def start_search(self):
        """开始搜索"""
        self.command_mode = True
        self.command_buffer = "/"
        self.draw_command_bar()
        self._process_command_input()
    
    def start_search_backward(self):
        """开始向后搜索"""
        self.command_mode = True
        self.command_buffer = "?"
        self.draw_command_bar()
        self._process_command_input()
    
    def next_search_result(self):
        """下一个搜索结果"""
        if not self.viewer.state.search_term:
            self.viewer.set_message("没有活动的搜索")
            return
            
        if not self.viewer.search_next():
            self.viewer.set_message("没有更多匹配项")
    
    def prev_search_result(self):
        """上一个搜索结果"""
        if not self.viewer.state.search_term:
            self.viewer.set_message("没有活动的搜索")
            return
            
        if not self.viewer.search_prev():
            self.viewer.set_message("没有更多匹配项")
    
    def start_save(self):
        """开始保存"""
        self.command_mode = True
        self.command_buffer = "s "
        self.draw_command_bar()
        self._process_command_input()
    
    def start_goto(self):
        """开始跳转"""
        self.command_mode = True
        self.command_buffer = "g"
        self.draw_command_bar()
        self._process_command_input()
    
    def scroll_up(self):
        """向上滚动"""
        self.viewer.scroll_up()
    
    def scroll_down(self):
        """向下滚动"""
        self.viewer.scroll_down()
    
    def scroll_up_page(self):
        """向上翻页"""
        self.viewer.page_up(self.height - 3)
    
    def scroll_down_page(self):
        """向下翻页"""
        self.viewer.page_down(self.height - 3)
    
    def toggle_full_view(self):
        """切换完整文件视图"""
        self.viewer.toggle_full_view()
    
    def toggle_line_numbers(self):
        """切换行号显示"""
        self.viewer.toggle_line_numbers()
    
    def toggle_highlight(self):
        """切换关键词高亮"""
        self.viewer.toggle_highlight()
    
    def filter_blocks(self):
        """过滤块"""
        if not self.viewer.state.search_term:
            self.viewer.set_message("请先使用 '/' 设置搜索词", True)
            return
            
        if not self.viewer.filter_blocks():
            self.viewer.set_message("没有找到匹配的块", True)
    
    def clear_filter(self):
        """清除过滤"""
        if self.viewer.state.filter_mode:
            self.viewer.clear_filter()
    
    def toggle_keyword_focus(self):
        """切换关键词聚焦"""
        # 确保偏移量与当前窗口高度匹配
        text_height = self.height - 3
        self.viewer.state.focus_offset = max(1, text_height // 3)
        self.viewer.toggle_keyword_focus()
    
    def increase_focus_offset(self):
        """增加关键词聚焦偏移量"""
        self.viewer.increase_focus_offset()
    
    def decrease_focus_offset(self):
        """减少关键词聚焦偏移量"""
        self.viewer.decrease_focus_offset() 