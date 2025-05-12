"""
命令行界面模块

提供命令行参数解析和程序入口功能。
"""

import argparse
import sys
import os
import curses
from .core.parser import LogParser
from .core.viewer import LogViewer
from .ui.curses_ui import CursesUI
from .plugins.quantum_chem import QuantumChemPlugin
from .utils.config import (
    load_separators, save_separators, DEFAULT_SEPARATORS,
    load_keyword_types, save_keyword_types, DEFAULT_KEYWORD_TYPES
)


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="LogView - VIM风格的日志查看器",
        epilog="使用VIM风格的按键进行导航和操作。按'h'获取帮助。"
    )
    
    parser.add_argument("filename", nargs="?", help="要打开的日志文件")
    parser.add_argument("--separator", "-s", help="使用的分隔符类型: grad, irc，默认为grad")
    parser.add_argument("--grad", action="store_true", help="使用Gaussian梯度分隔符")
    parser.add_argument("--irc", action="store_true", help="使用IRC分隔符")
    parser.add_argument("--version", "-v", action="store_true", help="显示版本信息")
    
    return parser.parse_args()


def print_keyboard_commands():
    """打印键盘命令说明"""
    print("""
LogView - VIM风格的日志查看器
==========================

导航命令:
  n / 右箭头 - 下一个块
  p / 左箭头 - 上一个块
  f - 第一个块
  l - 最后一个块
  g - 跳转到指定块 (例如: g10)
  j / 下箭头 - 向下滚动
  k / 上箭头 - 向上滚动
  J / PageDown - 向下翻页
  K / PageUp - 向上翻页

搜索和过滤:
  / - 开始搜索
    + Tab - 关键词补全（循环显示匹配的预设关键词）
  ? - 开始向后搜索 
    + Tab - 关键词补全（同上）
  N - 下一个搜索结果
  P - 上一个搜索结果
  F - 过滤模式 (只显示包含搜索词的块)
  O - 切换关键词聚焦 (过滤模式下自动聚焦关键词)
  + - 增加关键词聚焦偏移量 (关键词位置上移)
  - - 减少关键词聚焦偏移量 (关键词位置下移)
  c - 清除过滤

命令模式:
  :addkw - 添加当前搜索词到预设关键词列表
           (存储在 ~/.config/logview/keywords.json)

显示选项:
  v - 切换完整文件视图/分块视图
  # - 切换行号显示
  H - 切换关键词高亮

文件操作:
  s - 保存当前块到文件
  q - 退出程序
  
按任意键返回...
""")
    input()


def main():
    """主函数"""
    # 解析命令行参数
    args = parse_args()
    
    # 显示版本信息
    if args.version:
        print("LogView v1.0.0")
        return
    
    # 确保配置文件存在
    separators = load_separators()
    if separators == DEFAULT_SEPARATORS:
        save_separators(DEFAULT_SEPARATORS)
    
    keyword_types = load_keyword_types()
    if keyword_types == DEFAULT_KEYWORD_TYPES:
        save_keyword_types(DEFAULT_KEYWORD_TYPES)
    
    # 检查是否提供了文件名
    if not args.filename:
        print("错误: 未指定文件名")
        print("使用 'logview -h' 查看帮助")
        return
    
    # 检查文件是否存在
    if not os.path.exists(args.filename):
        print(f"错误: 文件 '{args.filename}' 不存在")
        return
    
    # 确定使用的分隔符
    separator_type = "grad"  # 默认值
    if args.separator:
        separator_type = args.separator
    elif args.grad:
        separator_type = "grad"
    elif args.irc:
        separator_type = "irc"
    
    # 创建量子化学插件，并检测文件类型
    quantum_plugin = QuantumChemPlugin("quantum_chem", "量子化学程序输出文件支持")
    
    # 检测是否为量子化学文件，并建议分隔符
    if quantum_plugin.detect_file_type(args.filename):
        suggested_separator = quantum_plugin.suggest_separator(args.filename)
        
        # 如果没有通过参数指定分隔符，则使用建议的分隔符
        if not (args.separator or args.grad or args.irc):
            separator = suggested_separator
        else:
            # 使用指定的分隔符
            separator = separators.get(separator_type, DEFAULT_SEPARATORS[separator_type])
    else:
        # 如果不是量子化学文件，则使用指定的分隔符
        separator = separators.get(separator_type, DEFAULT_SEPARATORS[separator_type])
    
    # 修正：直接初始化LogViewer，传入文件路径和分隔符
    viewer = LogViewer(args.filename, separator)
    
    # 初始化量子化学插件
    quantum_plugin.initialize(viewer)
    
    # 启动用户界面
    ui = CursesUI(viewer)
    
    try:
        ui.start()
    except KeyboardInterrupt:
        # 处理Ctrl+C退出
        print("程序被用户中断")
    except Exception as e:
        # 恢复终端状态后再报告错误
        curses.endwin()
        print(f"错误: {str(e)}")
        raise


if __name__ == "__main__":
    main() 