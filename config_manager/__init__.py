"""配置管理系统，用于管理和处理各种类型的配置。

该模块提供了一套灵活的机制来注册、解析、验证和组合不同类型的配置。
主要组件包括：

1. ConfigRegistry: 配置注册中心，用于管理不同类型的配置类
2. ConfigParser: 配置解析器，用于从命令行参数或配置文件解析配置
3. ConfigHelper: 配置辅助工具，提供配置对象的序列化、反序列化和类型转换等功能
4. CompositeConfig: 组合配置类，用于封装多个子配置，提供统一的访问接口

使用示例:
    >>> from config_manager import ConfigRegistry
    >>> @ConfigRegistry.register("model", "bert")
    >>> @dataclass
    >>> class BertConfig:
    >>>     hidden_size: int = 768
    >>>     num_layers: int = 12
"""

from .registry import ConfigRegistry
from .parser import ConfigParser
from .composite import CompositeConfig
from .helper import ConfigHelper

__all__ = ["ConfigRegistry", "ConfigParser", "CompositeConfig", "ConfigHelper"]
