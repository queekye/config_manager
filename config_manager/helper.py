from typing import Dict, Type, Any
import json
import yaml
from pathlib import Path


class ConfigHelper:
    """配置工具类，提供配置对象的通用功能。

    该类提供了配置对象的序列化、反序列化、类型转换等功能，
    可以在registry.py和parser.py中使用这些功能来增强配置类的能力。

    主要功能包括：
    1. 配置对象与字典之间的转换
    2. 配置对象的序列化与反序列化（支持JSON和YAML格式）
    3. 配置参数的自动类型转换和验证
    """

    @staticmethod
    def to_dict(config_obj) -> Dict[str, Any]:
        """将配置对象转换为字典格式。

        将配置对象的所有属性转换为字典，包括name属性（如果存在）。
        这个方法通常用于序列化配置对象。

        Args:
            config_obj: 配置对象实例，通常是dataclass实例

        Returns:
            Dict[str, Any]: 包含所有配置参数的字典

        示例:
            >>> @dataclass
            >>> class ModelConfig:
            >>>     hidden_size: int = 768
            >>>     name: str = "bert"
            >>> config = ModelConfig()
            >>> config_dict = ConfigHelper.to_dict(config)
            >>> print(config_dict)
            {'name': 'bert', 'hidden_size': 768}
        """
        result = {}
        # 如果name属性存在，则添加到结果中
        if hasattr(config_obj, "name"):
            result["name"] = config_obj.name
        # 更新其他属性
        result.update({k: v for k, v in config_obj.__dict__.items() if not k.startswith("_")})
        return result

    @staticmethod
    def save(config_obj, path: str) -> None:
        """将配置保存到文件。

        支持保存为 JSON 或 YAML 格式，根据文件扩展名自动选择格式。
        保存前会先将配置对象转换为字典格式。

        Args:
            config_obj: 配置对象实例
            path (str): 保存配置的文件路径，支持 .json、.yaml 或 .yml 扩展名

        Raises:
            ValueError: 当文件格式不支持时抛出

        示例:
            >>> config = ModelConfig(hidden_size=1024)
            >>> ConfigHelper.save(config, "config.json")
        """
        path = Path(path)
        if path.suffix == ".json":
            with open(path, "w", encoding="utf-8") as f:
                json.dump(
                    ConfigHelper.to_dict(config_obj), f, indent=2, ensure_ascii=False
                )
        elif path.suffix in {".yaml", ".yml"}:
            with open(path, "w", encoding="utf-8") as f:
                yaml.dump(ConfigHelper.to_dict(config_obj), f, allow_unicode=True)
        else:
            raise ValueError(f"不支持的文件格式：{path.suffix}")

    @staticmethod
    def load(config_cls: Type, path: str):
        """从文件加载配置。

        支持从 JSON 或 YAML 文件加载配置，根据文件扩展名自动选择格式。
        加载后会将数据传递给配置类的构造函数，创建配置对象实例。

        Args:
            config_cls (Type): 配置类，可以是dataclass或普通类
            path (str): 配置文件的路径，支持 .json、.yaml 或 .yml 扩展名

        Returns:
            配置对象实例

        Raises:
            ValueError: 当文件格式不支持时抛出

        示例:
            >>> config = ConfigHelper.load(ModelConfig, "config.json")
            >>> print(config.hidden_size)
            1024
        """
        path = Path(path)
        if path.suffix == ".json":
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        elif path.suffix in {".yaml", ".yml"}:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        else:
            raise ValueError(f"不支持的文件格式：{path.suffix}")
        return config_cls(**data)

    @staticmethod
    def post_init(config_obj):
        """配置对象初始化后的处理函数。

        执行参数的自动类型转换和验证，支持以下功能：
        1. 基本类型（int、float、bool、str）的转换
        2. 字符串到布尔值的转换（'true', 'yes', '1' 转换为 True）
        3. 逗号分隔的字符串到列表的转换
        4. JSON 字符串到字典的转换

        这个方法通常在创建配置对象后调用，用于确保所有参数的类型正确。
        对于从命令行参数或配置文件加载的配置，这个方法尤其重要，因为
        这些来源的数据通常是字符串类型，需要转换为正确的类型。

        Args:
            config_obj: 配置对象实例，必须是dataclass实例

        Returns:
            处理后的配置对象实例

        Raises:
            ValueError: 当参数值无法转换为目标类型时抛出

        示例:
            >>> @dataclass
            >>> class ModelConfig:
            >>>     hidden_size: int
            >>>     layers: list[int]
            >>> config = ModelConfig(hidden_size="768", layers="12,24,36")
            >>> config = ConfigHelper.post_init(config)
            >>> print(config.hidden_size, type(config.hidden_size))
            768 <class 'int'>
            >>> print(config.layers, type(config.layers))
            [12, 24, 36] <class 'list'>
        """
        for field_name, field in config_obj.__class__.__dataclass_fields__.items():
            value = getattr(config_obj, field_name)
            if value is not None:
                try:
                    # 处理基本类型
                    if field.type in {int, float, bool, str}:
                        if field.type == bool and isinstance(value, str):
                            # 字符串到布尔值的转换
                            value = value.lower() in {"true", "yes", "1"}
                        else:
                            # 其他基本类型的转换
                            value = field.type(value)
                    # 处理列表类型
                    elif field.type == list or (
                        hasattr(field.type, "__origin__")
                        and field.type.__origin__ is list
                    ):
                        if isinstance(value, str):
                            try:
                                # 尝试解析为JSON格式
                                items = json.loads(value)
                                if not isinstance(items, list):
                                    # 如果解析成功但不是列表，则按照逗号分隔处理
                                    items = value.split(",")
                            except json.JSONDecodeError:
                                # JSON解析失败，按照逗号分隔处理
                                items = value.split(",")

                            # 如果是泛型列表，获取元素类型；否则使用str类型
                            item_type = (
                                field.type.__args__[0]
                                if hasattr(field.type, "__args__")
                                else str
                            )
                            # 如果类型是Any，直接使用原值
                            if item_type == Any:
                                value = [
                                    item.strip() if isinstance(item, str) else item
                                    for item in items
                                ]
                            else:
                                value = [
                                    item_type(
                                        item.strip() if isinstance(item, str) else item
                                    )
                                    for item in items
                                ]
                        elif isinstance(value, (list, tuple)):
                            # 如果已经是列表或元组类型，确保元素类型正确
                            item_type = (
                                field.type.__args__[0]
                                if hasattr(field.type, "__args__")
                                else Any
                            )
                            # 如果类型是Any，直接使用原值
                            if item_type == Any:
                                value = list(value)
                            else:
                                value = [item_type(item) for item in value]
                    # 处理字典类型
                    elif field.type == dict or (
                        hasattr(field.type, "__origin__")
                        and field.type.__origin__ is dict
                    ):
                        if isinstance(value, str):
                            # 假设值是JSON格式的字符串
                            value = json.loads(value)
                        elif isinstance(value, dict):
                            # 如果已经是字典类型，确保键值类型正确
                            if hasattr(field.type, "__args__"):
                                key_type, value_type = field.type.__args__
                                # 如果类型是Any，直接使用原值
                                if key_type == Any:
                                    key_converter = lambda x: x
                                else:
                                    key_converter = key_type
                                if value_type == Any:
                                    value_converter = lambda x: x
                                else:
                                    value_converter = value_type
                                value = {
                                    key_converter(k): value_converter(v)
                                    for k, v in value.items()
                                }

                    setattr(config_obj, field_name, value)
                except (ValueError, TypeError, json.JSONDecodeError) as e:
                    raise ValueError(
                        f"参数 {field_name} 的值 {value} 无法转换为类型 {field.type}: {str(e)}"
                    )

        return config_obj
