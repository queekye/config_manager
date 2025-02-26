from dataclasses import dataclass
from typing import Dict, Any

from .base import BaseConfig

@dataclass
class CompositeConfig(BaseConfig):
    
    """组合配置类，用于封装多个子配置。

    该类继承自BaseConfig，提供了通过属性访问子配置的功能，
    并为每个子配置类型添加对应的type属性。

    示例:
        >>> configs = CompositeConfig()
        >>> configs.model.hidden_size  # 访问模型配置的参数
        >>> configs.model_type  # 获取模型类型
    """
    name: str = "composite"
    
    def __init__(self, **configs):
        """初始化组合配置类。
    
        Args:
            name: 配置名称
            **configs: 子配置对象字典，键为配置类型
        """
        self._configs = configs
    
        # 为每个配置类型添加type属性
        for config_type, config in configs.items():
            if hasattr(config, "name"):
                setattr(self, f"{config_type}_name", config.name)

    def __getattr__(self, name: str) -> Any:
        """通过属性访问子配置。

        Args:
            name: 属性名称

        Returns:
            子配置对象或属性值

        Raises:
            AttributeError: 当属性不存在时抛出
        """
        if name in self._configs:
            return self._configs[name]
        raise AttributeError(f"'{self.__class__.__name__}' 对象没有属性 '{name}'")

    def to_dict(self) -> Dict[str, Any]:
        """将配置对象转换为字典格式。

        Returns:
            Dict[str, Any]: 包含所有配置参数的字典
        """
        result = super().to_dict()
        # 添加子配置
        for config_type, config in self._configs.items():
            if hasattr(config, "to_dict"):
                result[config_type] = config.to_dict()
            if hasattr(config, "name"):
                result[f"{config_type}_name"] = config.name
        
        # 过滤掉以_开头的键
        filtered_result = {}
        for key, value in result.items():
            if key.startswith('_'):
                continue
            if isinstance(value, dict):
                # 过滤嵌套字典中以_开头的键
                filtered_dict = {}
                for sub_key, sub_value in value.items():
                    if not sub_key.startswith('_'):
                        filtered_dict[sub_key] = sub_value
                if filtered_dict:
                    filtered_result[key] = filtered_dict
            else:
                filtered_result[key] = value
                
        return filtered_result
    
    def __str__(self):
        """重写__str__方法，使其返回配置的字典形式的字符串表示"""
        config_dict = self.to_dict()
        # 格式化输出配置字典
        lines = []
        for key, value in config_dict.items():
            if isinstance(value, dict):
                # 处理嵌套字典，增加缩进
                sub_lines = [f"{key}:"]
                for sub_key, sub_value in value.items():
                    sub_lines.append(f"    {sub_key}: {sub_value}")
                lines.extend(sub_lines)
            else:
                lines.append(f"{key}: {value}")
        return "\n".join(lines)

    def __repr__(self):
        """重写__repr__方法，使其返回配置的字典形式的字符串表示"""
        return self.__str__()