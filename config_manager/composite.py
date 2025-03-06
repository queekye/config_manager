from dataclasses import dataclass
from typing import Dict, Any
from pathlib import Path
import json
import yaml
from .helper import ConfigHelper


@dataclass
class CompositeConfig:
    """组合配置类，用于封装多个子配置。

    提供了通过属性访问子配置的功能，并为每个子配置类型添加对应的name属性。
    这个类是配置管理系统的核心，它将多个不同类型的配置组合在一起，提供统一的访问接口。

    主要功能包括：
    1. 通过属性访问子配置（如 config.model.hidden_size）
    2. 为每个子配置类型添加对应的name属性（如 config.model_name）
    3. 将配置转换为字典格式，用于序列化
    4. 将配置保存到文件（支持JSON和YAML格式）

    示例:
        >>> configs = CompositeConfig(model=model_config, task=task_config)
        >>> configs.model.hidden_size  # 访问模型配置的参数
        >>> configs.model_name  # 获取模型名称
    """

    name: str = "composite"

    def __init__(self, **configs):
        """初始化组合配置类。

        Args:
            **configs: 子配置对象字典，键为配置类型，值为配置对象实例

        示例:
            >>> model_config = ModelConfig(hidden_size=768)
            >>> task_config = TaskConfig(num_classes=10)
            >>> configs = CompositeConfig(model=model_config, task=task_config)
        """
        self._configs = configs

        # 为每个配置类型添加name属性
        for config_type, config in configs.items():
            if hasattr(config, "name"):
                setattr(self, f"{config_type}_name", config.name)

    def __getattr__(self, name: str) -> Any:
        """通过属性访问子配置。

        允许通过属性名直接访问子配置对象，如 config.model 将返回模型配置对象。
        这种方式比字典访问更加直观和方便。

        Args:
            name: 属性名称，通常是配置类型名称

        Returns:
            子配置对象或属性值

        Raises:
            AttributeError: 当属性不存在时抛出

        示例:
            >>> configs = CompositeConfig(model=model_config)
            >>> model = configs.model  # 获取模型配置对象
            >>> hidden_size = configs.model.hidden_size  # 获取模型配置的参数
        """
        if name in self._configs:
            return self._configs[name]
        raise AttributeError(f"'{self.__class__.__name__}' 对象没有属性 '{name}'")

    def to_dict(self) -> Dict[str, Any]:
        """将配置对象转换为字典格式。

        将所有子配置对象转换为嵌套字典，并添加配置类型名称。
        这个方法通常用于序列化配置对象，以便保存到文件或传输。

        转换规则：
        1. 每个子配置对象都会被转换为字典，并以配置类型为键存储
        2. 每个子配置的name属性会被单独存储，键名为 "{config_type}_name"
        3. 以下划线开头的属性会被过滤掉，不会出现在结果中

        Returns:
            Dict[str, Any]: 包含所有配置参数的字典

        示例:
            >>> configs = CompositeConfig(model=model_config, task=task_config)
            >>> config_dict = configs.to_dict()
            >>> print(config_dict)
            {
                'model': {'hidden_size': 768, 'name': 'bert'},
                'model_name': 'bert',
                'task': {'num_classes': 10, 'name': 'classification'},
                'task_name': 'classification'
            }
        """
        result = {}
        # 添加子配置
        for config_type, config in self._configs.items():
            result[config_type] = ConfigHelper.to_dict(config)
            if hasattr(config, "name"):
                result[f"{config_type}_name"] = config.name

        # 过滤掉以_开头的键
        filtered_result = {}
        for key, value in result.items():
            if key.startswith("_"):
                continue
            if isinstance(value, dict):
                # 过滤嵌套字典中以_开头的键
                filtered_dict = {}
                for sub_key, sub_value in value.items():
                    if not sub_key.startswith("_"):
                        filtered_dict[sub_key] = sub_value
                if filtered_dict:
                    filtered_result[key] = filtered_dict
            else:
                filtered_result[key] = value

        return filtered_result

    def __str__(self):
        """重写__str__方法，使其返回配置的字典形式的字符串表示。

        返回的字符串是格式化的配置字典，每个配置类型和参数都占一行，
        嵌套的配置会有缩进，便于阅读。

        Returns:
            str: 配置的字符串表示

        示例:
            >>> configs = CompositeConfig(model=model_config)
            >>> print(configs)
            model:
                hidden_size: 768
                name: bert
            model_name: bert
        """
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
        """重写__repr__方法，使其返回配置的字典形式的字符串表示。

        与__str__方法相同，返回格式化的配置字典字符串。

        Returns:
            str: 配置的字符串表示
        """
        return self.__str__()
    
    @property
    def __dict__(self):
        """将配置对象转换为字典格式。

        与to_dict方法相同，返回包含所有配置参数的字典。
        """
        return self.to_dict()

    def save(self, path: str) -> None:
        """将配置保存到文件。

        支持保存为 JSON 或 YAML 格式，根据文件扩展名自动选择格式。
        内部调用ConfigHelper.save方法实现保存功能。

        Args:
            path (str): 保存配置的文件路径，支持 .json、.yaml 或 .yml 扩展名

        Raises:
            ValueError: 当文件格式不支持时抛出

        示例:
            >>> configs = CompositeConfig(model=model_config)
            >>> configs.save("config.json")
        """
        ConfigHelper.save(self, path)
