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


def parse_args() -> argparse.Namespace:
    """
    解析命令行参数
    
    Returns:
        argparse.Namespace: 解析后的参数
    """
    parser = argparse.ArgumentParser(
        description='LogView - 基于VIM风格的通用日志查看器'
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
        '--version', 
        action='version',
        version='%(prog)s 0.1.0'
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