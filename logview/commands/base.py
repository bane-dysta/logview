"""
命令基础类模块

提供命令定义、注册和执行的基础架构。
"""

from typing import Dict, List, Callable, Any, Optional
from abc import ABC, abstractmethod


class Command(ABC):
    """命令基类，所有命令都应继承此类"""
    
    def __init__(self, name: str, description: str, handler: Callable):
        """
        初始化命令
        
        Args:
            name: 命令名称
            description: 命令描述
            handler: 命令处理函数
        """
        self.name = name
        self.description = description
        self.handler = handler
    
    @abstractmethod
    def execute(self, *args, **kwargs) -> Any:
        """
        执行命令
        
        应由子类实现实际的执行逻辑
        
        Returns:
            Any: 命令执行结果
        """
        pass


class CommandManager:
    """命令管理器，负责命令的注册和查找"""
    
    def __init__(self):
        """初始化命令管理器"""
        self.commands: Dict[str, Command] = {}
        self.aliases: Dict[str, str] = {}
    
    def register_command(self, command: Command) -> None:
        """
        注册命令
        
        Args:
            command: 要注册的命令对象
        """
        self.commands[command.name] = command
    
    def register_alias(self, alias: str, command_name: str) -> bool:
        """
        注册命令别名
        
        Args:
            alias: 别名
            command_name: 对应的命令名称
            
        Returns:
            bool: 是否成功注册别名
        """
        if command_name in self.commands:
            self.aliases[alias] = command_name
            return True
        return False
    
    def get_command(self, name: str) -> Optional[Command]:
        """
        获取命令对象
        
        Args:
            name: 命令名称或别名
            
        Returns:
            Optional[Command]: 命令对象，如果未找到则返回None
        """
        if name in self.commands:
            return self.commands[name]
        
        if name in self.aliases:
            return self.commands[self.aliases[name]]
        
        return None
    
    def execute_command(self, name: str, *args, **kwargs) -> Any:
        """
        执行命令
        
        Args:
            name: 命令名称或别名
            *args: 传递给命令的位置参数
            **kwargs: 传递给命令的关键字参数
            
        Returns:
            Any: 命令执行结果
            
        Raises:
            ValueError: 如果命令未找到
        """
        command = self.get_command(name)
        if command:
            return command.execute(*args, **kwargs)
        
        raise ValueError(f"未找到命令: {name}")
    
    def get_all_commands(self) -> List[Command]:
        """
        获取所有注册的命令
        
        Returns:
            List[Command]: 命令列表
        """
        return list(self.commands.values()) 