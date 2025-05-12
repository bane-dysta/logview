"""
命令行界面入口模块

提供命令行参数解析和程序入口点。
"""

import argparse
import sys
import os
import curses
import traceback
from typing import List, Optional

from .core.viewer import LogViewer
from .ui.curses_ui import CursesUI
from .plugins.base import PluginManager
from .plugins.quantum_chem import QuantumChemPlugin


def print_keyboard_commands():
    """显示所有可用的键盘命令"""
    keyboard_help = """
LogView 键盘命令:
=============================================

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
  h - 显示帮助信息

文件操作:
  s - 保存当前块到文件
  q - 退出程序
"""
    print(keyboard_help)


def parse_args() -> argparse.Namespace:
    """
    解析命令行参数
    
    Returns:
        argparse.Namespace: 解析后的参数
    """
    parser = argparse.ArgumentParser(
        description='LogView - VIM风格的通用量子化学日志文件查看器',
        epilog='运行时使用VIM风格键盘命令进行导航和操作。使用-k或--keys查看所有键盘命令。'
    )
    
    parser.add_argument(
        'filename', 
        nargs='?', 
        help='要打开的日志文件路径'
    )
    
    parser.add_argument(
        '-s', '--separator', 
        help='用于分块的分隔符'
    )
    
    parser.add_argument(
        '-g', '--grad', 
        action='store_true',
        help='使用Grad分隔符 (量子化学计算)'
    )
    
    parser.add_argument(
        '-i', '--irc', 
        action='store_true',
        help='使用IRC分隔符 (量子化学计算)'
    )
    
    parser.add_argument(
        '-k', '--keys',
        action='store_true',
        help='显示所有可用的键盘命令'
    )
    
    parser.add_argument(
        '--version', 
        action='version',
        version='%(prog)s 0.2.0'
    )
    
    return parser.parse_args()


def main(argv: Optional[List[str]] = None) -> int:
    """
    程序主入口函数
    
    Args:
        argv: 命令行参数，如果为None则使用sys.argv
        
    Returns:
        int: 退出码
    """
    if argv is None:
        argv = sys.argv[1:]
        
    args = parse_args()
    
    # 如果指定了-k/--keys参数，显示键盘命令并退出
    if args.keys:
        print_keyboard_commands()
        return 0
    
    # 如果没有提供文件名且没有其他参数，打印简短帮助
    if not args.filename and not (args.separator or args.grad or args.irc):
        print("LogView - 基于VIM风格的通用日志查看器\n")
        print("用法: logview [选项] 文件路径")
        print("尝试 'logview --help' 获取更多信息")
        print("使用 'logview --keys' 查看所有键盘命令")
        return 0
    
    # 检查要打开的文件是否存在
    if args.filename and not os.path.exists(args.filename):
        print(f"错误: 文件不存在: {args.filename}")
        return 1
    
    # 根据参数确定使用的分隔符
    separator = None
    if args.separator:
        separator = args.separator
    elif args.grad:
        separator = QuantumChemPlugin.SEPARATORS["grad"]
    elif args.irc:
        separator = QuantumChemPlugin.SEPARATORS["irc"]
    
    try:
        # 初始化查看器
        viewer = LogViewer(args.filename, separator)
        
        # 创建插件管理器并加载量子化学插件
        plugin_manager = PluginManager()
        plugin_manager.register_plugin_class(QuantumChemPlugin)
        
        # 如果提供了文件名，尝试检测文件类型并加载相应插件
        if args.filename:
            # 自动检测文件类型
            quantum_plugin = QuantumChemPlugin("quantum_chem", "量子化学程序输出文件支持")
            if quantum_plugin.detect_file_type(args.filename):
                # 如果是量子化学文件且未指定分隔符，使用建议的分隔符
                if not separator:
                    suggested_separator = quantum_plugin.suggest_separator(args.filename)
                    viewer.parser.set_separator("custom", suggested_separator)
                    viewer.parser.parse()
                    viewer.reset_state()
                
                # 初始化插件
                quantum_plugin.initialize(viewer)
        
        # 创建并启动UI
        ui = CursesUI(viewer)
        ui.start()
        
        return 0
        
    except KeyboardInterrupt:
        # 处理Ctrl+C
        print("\n程序已终止")
        return 130
    except Exception as e:
        # 捕获其他异常
        print(f"发生错误: {str(e)}")
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main()) 