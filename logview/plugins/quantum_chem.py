"""
量子化学程序输出插件

为量子化学程序(如Gaussian、ORCA等)的输出文件提供特定功能。
"""

from typing import Dict, List, Any
from .base import Plugin
import re


class QuantumChemPlugin(Plugin):
    """量子化学程序输出文件插件"""
    
    name = "quantum_chem"
    description = "量子化学程序输出文件支持"
    
    # 定义常见分隔符
    SEPARATORS = {
        "grad": "GradGradGradGradGradGradGradGradGradGradGradGradGradGradGradGradGradGrad",
        "irc": "IRC-IRC-IRC-IRC-IRC-IRC-IRC-IRC-IRC-IRC-IRC-IRC-IRC-IRC-IRC-IRC-IRC-IRC",
    }
    
    # 常见的量子化学关键词
    COMMON_KEYWORDS = [
        "SCF Done", "Excited State   1", "Optimization completed", "normal coordinates",
        "Orbital symmetries", "Mulliken charges", "APT charges:", "Converged?", 
        "Standard orientation", "Input orientation", "Frequency", "Failed", 
        "dipole moments", "Point Number:"
    ]
    
    # 错误关键词
    ERROR_KEYWORDS = ["Error", "Failed", "错误", "失败"]
    
    # 警告关键词
    WARNING_KEYWORDS = ["Warning", "警告"]
    
    # 成功关键词
    SUCCESS_KEYWORDS = ["SCF Done", "Optimization completed", "Converged"]
    
    def __init__(self, name: str, description: str):
        """初始化插件"""
        super().__init__(name, description)
        self.viewer = None
        self.highlighter = None
    
    def initialize(self, context: Any) -> None:
        """
        初始化插件
        
        Args:
            context: 包含应用程序组件的上下文
        """
        # 保存对LogViewer的引用
        self.viewer = context
        self.highlighter = context.highlighter
        
        # 添加量子化学特定的高亮模式
        self._setup_highlight_patterns()
    
    def _setup_highlight_patterns(self) -> None:
        """设置量子化学特定的高亮模式"""
        if not self.highlighter:
            return
            
        # 清除现有模式，使用量子化学特定的模式
        self.highlighter.clear_patterns()
        
        # 添加错误关键词高亮
        for keyword in self.ERROR_KEYWORDS:
            self.highlighter.add_pattern(
                keyword,
                self.highlighter.DEFAULT_STYLES["error"],
                whole_line=True,
                case_sensitive=False
            )
        
        # 添加警告关键词高亮
        for keyword in self.WARNING_KEYWORDS:
            self.highlighter.add_pattern(
                keyword,
                self.highlighter.DEFAULT_STYLES["warning"],
                whole_line=True,
                case_sensitive=False
            )
        
        # 添加成功关键词高亮
        for keyword in self.SUCCESS_KEYWORDS:
            self.highlighter.add_pattern(
                keyword,
                self.highlighter.DEFAULT_STYLES["success"],
                whole_line=True,
                case_sensitive=False
            )
        
        # 添加常见关键词高亮
        for keyword in self.COMMON_KEYWORDS:
            self.highlighter.add_pattern(
                keyword,
                self.highlighter.DEFAULT_STYLES["keyword"],
                whole_line=False,
                case_sensitive=False
            )
    
    def detect_file_type(self, filename: str) -> bool:
        """
        检测文件是否为量子化学程序输出文件
        
        Args:
            filename: 文件路径
            
        Returns:
            bool: 是否为量子化学程序输出文件
        """
        try:
            with open(filename, 'r', encoding='utf-8', errors='ignore') as file:
                # 读取前1000行或文件结束
                lines = []
                for i, line in enumerate(file):
                    lines.append(line)
                    if i >= 1000:
                        break
                
                content = ''.join(lines)
                
                # 检查是否包含量子化学软件的特征字符串
                patterns = [
                    "Gaussian",
                    "ORCA",
                    "GAMESS",
                    "Molpro",
                    "Q-Chem",
                    "NWChem",
                    "SCF Done",
                    "Optimization completed",
                    "Convergence criterion met"
                ]
                
                for pattern in patterns:
                    if pattern in content:
                        return True
                
            return False
        except:
            return False
    
    def suggest_separator(self, filename: str) -> str:
        """
        根据文件内容建议使用的分隔符
        
        Args:
            filename: 文件路径
            
        Returns:
            str: 建议的分隔符
        """
        try:
            with open(filename, 'r', encoding='utf-8', errors='ignore') as file:
                content = file.read(10000)  # 读取前10000个字符
                
                # 检查是否包含IRC计算
                if "IRC" in content and "--IRC--" in content:
                    return self.SEPARATORS["irc"]
                
                # 默认使用Grad分隔符
                return self.SEPARATORS["grad"]
        except:
            # 出现错误时使用默认分隔符
            return self.SEPARATORS["grad"]
    
    def extract_energy(self, block: str) -> float:
        """
        从块中提取能量值
        
        Args:
            block: 文本块内容
            
        Returns:
            float: 提取的能量值，如果未找到则返回None
        """
        # 尝试匹配SCF能量
        scf_match = re.search(r"SCF Done:.*=\s*([-]?\d+\.\d+)", block)
        if scf_match:
            return float(scf_match.group(1))
        
        # 尝试匹配最终能量
        final_match = re.search(r"Energy=\s*([-]?\d+\.\d+)", block)
        if final_match:
            return float(final_match.group(1))
        
        return None
    
    def extract_geometries(self, block: str) -> List[Dict]:
        """
        从块中提取分子几何结构
        
        Args:
            block: 文本块内容
            
        Returns:
            List[Dict]: 提取的几何结构列表，每个几何结构为原子符号和坐标的字典
        """
        geometries = []
        
        # 匹配标准坐标块
        std_orient_matches = re.finditer(
            r"Standard orientation:.*?-+\n.*?-+\n(.*?)(?:-+|Rotational constants)",
            block, re.DOTALL
        )
        
        for match in std_orient_matches:
            geometry = {}
            lines = match.group(1).strip().split('\n')
            for line in lines:
                parts = line.strip().split()
                if len(parts) >= 6:  # 应至少包含6列数据
                    try:
                        atom_num = int(parts[1])
                        atom_sym = parts[3]
                        x = float(parts[3])
                        y = float(parts[4])
                        z = float(parts[5])
                        geometry[atom_sym] = (x, y, z)
                    except (ValueError, IndexError):
                        pass
            
            if geometry:
                geometries.append(geometry)
        
        return geometries
    
    def cleanup(self) -> None:
        """清理插件资源"""
        # 重置高亮器
        if self.highlighter:
            self.highlighter.reset_to_defaults() 