from typing import Dict, Type, Optional, Set, List, Any
import dataclasses
import json
import yaml
from pathlib import Path


class ConfigRegistry:
    """配置注册中心，用于管理不同类型的配置类。

    该类提供了一个统一的配置注册机制，支持注册任意类型的配置类。所有注册的配置类都会被存储在一个统一的字典中，
    并通过配置类型和名称进行索引。同时提供了参数冲突检查、配置验证等功能。

    属性:
        _configs (Dict[str, Dict[str, Type]]): 存储所有注册的配置类，格式为 {config_type: {name: config_class}}
        exclude_params (Set[str]): 排除参数集合，这些参数在冲突检查时会被排除

    示例:
        >>> @ConfigRegistry.register("model", "bert")
        >>> @dataclass
        >>> class BertConfig:
        >>>     hidden_size: int = 768
        >>>     num_layers: int = 12
    """

    _configs: Dict[str, Dict[str, Type]] = {}
    exclude_params: Set[str] = set(["name"])

    @classmethod
    def register(cls, config_type: str, name: str):
        """注册配置类的装饰器。

        用于将配置类注册到配置中心，支持通过装饰器语法进行注册。注册时会进行参数冲突检查，
        确保不同类型的配置之间不会出现参数名冲突。

        Args:
            config_type (str): 配置类型，如 'model', 'task', 'training' 等
            name (str): 配置名称，用于唯一标识该类型下的配置

        Returns:
            callable: 装饰器函数

        Raises:
            ValueError: 当存在参数冲突时抛出，或当尝试重复注册相同类型和名称的配置类时抛出
            TypeError: 当配置类不是dataclass时抛出

        示例:
            >>> @ConfigRegistry.register("model", "bert")
            >>> class BertConfig:
            >>>     hidden_size: int = 768
        """

        def wrapper(config_cls: Type) -> Type:
            if not hasattr(config_cls, "__dataclass_fields__"):
                raise TypeError(
                    f"配置类必须使用@dataclass装饰器定义，得到的是 {config_cls}"
                )

            # 检查是否存在重复注册
            if config_type in cls._configs and name in cls._configs[config_type]:
                raise ValueError(
                    f"配置类型 '{config_type}' 下已存在名为 '{name}' 的配置类"
                )

            # 检查参数冲突
            cls._check_param_conflicts(config_cls, config_type, name)

            # 确保配置类型的字典存在
            if config_type not in cls._configs:
                cls._configs[config_type] = {}

            cls._configs[config_type][name] = config_cls

            config_cls.name = name
            return config_cls

        return wrapper

    @classmethod
    def get_config(cls, config_type: str, name: str) -> Optional[Type]:
        """获取指定类型和名称的配置类。

        Args:
            config_type (str): 配置类型，如 'model', 'task' 等
            name (str): 配置名称

        Returns:
            Optional[Type[]]: 配置类，如果不存在则返回 None

        示例:
            >>> config_cls = ConfigRegistry.get_config("model", "bert")
            >>> config = config_cls(hidden_size=1024)
        """
        return cls._configs.get(config_type, {}).get(name)

    @classmethod
    def list_available_configs(cls) -> Dict[str, List[str]]:
        """列出所有可用的配置类。

        Returns:
            Dict[str, List[str]]: 配置类型及其对应的配置名称列表，格式为 {config_type: [name1, name2, ...]}

        示例:
            >>> configs = ConfigRegistry.list_available_configs()
            >>> print(configs)
            {'model': ['bert', 'gpt'], 'task': ['classification']}
        """
        return {
            config_type: list(configs.keys())
            for config_type, configs in cls._configs.items()
        }

    @classmethod
    def get_config_params(cls, config_type: str, name: str) -> Dict[str, str]:
        """获取指定配置类的参数说明。

        Args:
            config_type (str): 配置类型
            name (str): 配置名称

        Returns:
            Dict[str, str]: 参数名称及其说明的字典，格式为 {param_name: param_doc}

        Raises:
            ValueError: 当指定的配置类不存在时抛出

        示例:
            >>> params = ConfigRegistry.get_config_params("model", "bert")
            >>> print(params)
            {'hidden_size': '隐藏层大小', 'num_layers': '层数'}
        """
        config_cls = cls.get_config(config_type, name)
        if config_cls is None:
            raise ValueError(f"未找到配置：{config_type}/{name}")

        return cls._get_param_docs(config_cls)

    @classmethod
    def validate_and_assign_params(
        cls,
        config_types: Dict[str, str],
        params: Dict[str, any],
        valid_missing: bool = True,
    ) -> Dict[str, Dict[str, any]]:
        """验证并分配参数到相应的配置类。

        Args:
            config_types (Dict[str, str]): 配置类型及其名称的映射，如 {"model": "bert", "task": "classification"}
            params (Dict[str, any]): 要分配的参数字典，格式为 {param_name: param_value}
            valid_missing (bool): 是否验证缺少的参数，默认为True

        Returns:
            Dict[str, Dict[str, any]]: 分配后的参数字典，格式为 {config_type: {param_name: param_value}}

        Raises:
            ValueError: 当存在无效的配置名称、未分配的参数或缺少必需参数时抛出

        示例:
            >>> assigned = ConfigRegistry.validate_and_assign_params(
            >>>     {"model": "bert", "task": "classification"},
            >>>     {"hidden_size": 1024, "num_classes": 10}
            >>> )
            >>> print(assigned)
            {'model': {'hidden_size': 1024}, 'task': {'num_classes': 10}}
        """
        # 获取所有配置类
        config_classes = {}
        for config_type, name in config_types.items():
            config_cls = cls.get_config(config_type, name)
            if config_cls is None:
                raise ValueError(f"Invalid config: {config_type}/{name}")
            config_classes[config_type] = config_cls

        # 获取各配置类的参数集合
        config_params = {
            config_type: set(cls._get_param_names(config_cls))
            for config_type, config_cls in config_classes.items()
        }

        # 分配参数
        assigned_params = {config_type: {} for config_type in config_types}
        unassigned_params = set()

        for param_name, param_value in params.items():
            assigned = False
            for config_type, param_set in config_params.items():
                if param_name in param_set:
                    assigned_params[config_type][param_name] = param_value
                    assigned = True

            if not assigned:
                unassigned_params.add(param_name)

        # 检查必需参数
        missing_params = []
        for config_type, config_cls in config_classes.items():
            for param_name in cls._get_required_params(config_cls):
                if (
                    param_name not in assigned_params[config_type]
                    and param_name not in cls.exclude_params
                ):
                    missing_params.append(f"{config_type}.{param_name}")
        if unassigned_params:
            raise ValueError(f"未分配的参数: {', '.join(unassigned_params)}")
        if valid_missing and missing_params:
            raise ValueError(f"缺少必需参数: {', '.join(missing_params)}")

        return assigned_params

    @classmethod
    def _check_param_conflicts(
        cls, config_cls: Type, config_type: str, name: str
    ) -> None:
        """检查参数冲突。

        检查规则：
        1. 不同类型的配置类之间不能有重名参数
        2. 同类型的配置类之间允许有重名参数

        Args:
            config_cls (Type): 要检查的配置类
            config_type (str): 配置类型
            name (str): 配置名称

        Raises:
            ValueError: 当存在参数冲突时抛出
        """
        new_params = set(cls._get_param_names(config_cls))
        base_params = set(["name"])  # 不再需要获取基类参数

        # 检查与其他类型配置的参数冲突
        for other_type, other_configs in cls._configs.items():
            if other_type != config_type:  # 跳过同类型的配置
                for other_name, other_cls in other_configs.items():
                    other_params = set(cls._get_param_names(other_cls))
                    # 排除基类参数后再检查冲突
                    conflicts = (new_params - base_params - cls.exclude_params) & (
                        other_params - base_params - cls.exclude_params
                    )
                    if conflicts:
                        raise ValueError(
                            f"参数冲突：{config_type} 配置 '{name}' 与 {other_type} 配置 '{other_name}' 存在重名参数: {conflicts}"
                        )

    @staticmethod
    def _get_param_names(cls: Type) -> Set[str]:
        """获取类的所有参数名称。

        Args:
            cls (Type): 要获取参数的类

        Returns:
            Set[str]: 参数名称集合
        """
        return {name for name, _ in cls.__dataclass_fields__.items()}

    @staticmethod
    def _get_required_params(cls: Type) -> Set[str]:
        """获取类的必需参数名称。

        必需参数是指在dataclass中没有默认值的字段。

        Args:
            cls (Type): 要获取必需参数的类

        Returns:
            Set[str]: 必需参数名称集合
        """
        required_params = set()
        for name, field in cls.__dataclass_fields__.items():
            if (
                field.default == dataclasses.MISSING
                and field.default_factory == dataclasses.MISSING
            ):
                required_params.add(name)
        return required_params

    @staticmethod
    def _get_param_docs(cls: Type) -> Dict[str, str]:
        """获取类的参数文档说明。

        从类的docstring中提取参数说明，格式为：
        Args:
            param_name: 参数说明

        Args:
            cls (Type): 要获取参数文档的类

        Returns:
            Dict[str, str]: 参数名称及其说明的字典
        """
        return {name: field.metadata.get('help', '') 
        for name, field in cls.__dataclass_fields__.items()}
