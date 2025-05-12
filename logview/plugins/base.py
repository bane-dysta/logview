"""
插件基础类模块

定义插件的基础接口和加载机制。
"""

from typing import Dict, List, Any, Optional, Type
from abc import ABC, abstractmethod
import importlib
import os
import sys
import inspect


class Plugin(ABC):
    """插件基类，所有插件必须继承此类"""
    
    def __init__(self, name: str, description: str):
        """
        初始化插件
        
        Args:
            name: 插件名称
            description: 插件描述
        """
        self.name = name
        self.description = description
        self.enabled = True
    
    @abstractmethod
    def initialize(self, context: Any) -> None:
        """
        初始化插件
        
        Args:
            context: 插件上下文，通常包含应用程序的主要组件引用
        """
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """清理插件资源"""
        pass
    
    def enable(self) -> None:
        """启用插件"""
        self.enabled = True
    
    def disable(self) -> None:
        """禁用插件"""
        self.enabled = False
    
    def is_enabled(self) -> bool:
        """
        检查插件是否启用
        
        Returns:
            bool: 插件是否启用
        """
        return self.enabled


class PluginManager:
    """插件管理器，负责插件的加载、注册和管理"""
    
    def __init__(self):
        """初始化插件管理器"""
        self.plugins: Dict[str, Plugin] = {}
        self.plugin_classes: Dict[str, Type[Plugin]] = {}
    
    def register_plugin_class(self, plugin_class: Type[Plugin]) -> None:
        """
        注册插件类
        
        Args:
            plugin_class: 插件类
        """
        if issubclass(plugin_class, Plugin) and plugin_class is not Plugin:
            instance = plugin_class(
                getattr(plugin_class, 'name', plugin_class.__name__),
                getattr(plugin_class, 'description', '')
            )
            self.plugin_classes[instance.name] = plugin_class
    
    def discover_plugins(self, plugins_dir: str = None) -> None:
        """
        发现插件目录中的插件
        
        Args:
            plugins_dir: 插件目录路径，如果为None则使用当前模块的目录
        """
        if plugins_dir is None:
            # 使用当前模块的目录
            plugins_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 添加插件目录到系统路径
        if plugins_dir not in sys.path:
            sys.path.insert(0, plugins_dir)
        
        # 遍历目录中的Python文件
        for filename in os.listdir(plugins_dir):
            if filename.endswith('.py') and not filename.startswith('__'):
                module_name = filename[:-3]
                try:
                    # 导入模块
                    module = importlib.import_module(module_name)
                    
                    # 查找模块中的插件类
                    for name, obj in inspect.getmembers(module):
                        if inspect.isclass(obj) and issubclass(obj, Plugin) and obj is not Plugin:
                            self.register_plugin_class(obj)
                            
                except (ImportError, AttributeError) as e:
                    print(f"加载插件 {module_name} 时出错: {e}")
    
    def load_plugin(self, name: str, context: Any) -> Optional[Plugin]:
        """
        加载并初始化插件
        
        Args:
            name: 插件名称
            context: 传递给插件初始化方法的上下文
            
        Returns:
            Optional[Plugin]: 加载的插件实例，如果加载失败则返回None
        """
        if name in self.plugin_classes:
            try:
                plugin = self.plugin_classes[name](name, getattr(self.plugin_classes[name], 'description', ''))
                plugin.initialize(context)
                self.plugins[name] = plugin
                return plugin
            except Exception as e:
                print(f"初始化插件 {name} 时出错: {e}")
                return None
        return None
    
    def load_all_plugins(self, context: Any) -> None:
        """
        加载所有已注册的插件
        
        Args:
            context: 传递给插件初始化方法的上下文
        """
        for name in list(self.plugin_classes.keys()):
            self.load_plugin(name, context)
    
    def get_plugin(self, name: str) -> Optional[Plugin]:
        """
        获取已加载的插件
        
        Args:
            name: 插件名称
            
        Returns:
            Optional[Plugin]: 插件实例，如果未找到则返回None
        """
        return self.plugins.get(name)
    
    def get_all_plugins(self) -> List[Plugin]:
        """
        获取所有已加载的插件
        
        Returns:
            List[Plugin]: 插件列表
        """
        return list(self.plugins.values())
    
    def unload_plugin(self, name: str) -> bool:
        """
        卸载插件
        
        Args:
            name: 插件名称
            
        Returns:
            bool: 是否成功卸载
        """
        if name in self.plugins:
            try:
                self.plugins[name].cleanup()
                del self.plugins[name]
                return True
            except Exception as e:
                print(f"卸载插件 {name} 时出错: {e}")
        return False
    
    def unload_all_plugins(self) -> None:
        """卸载所有插件"""
        for name in list(self.plugins.keys()):
            self.unload_plugin(name) 