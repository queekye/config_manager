import argparse
from pathlib import Path
import json
import yaml
from typing import Tuple, Dict, Any

from .registry import ConfigRegistry
from .composite import CompositeConfig
from .helper import ConfigHelper


class ConfigParser:
    """配置解析器，用于从命令行参数或配置文件解析配置。

    该类提供了一个统一的配置解析机制，支持从命令行参数或配置文件解析配置。
    支持以下命令：
    - list: 列出所有可用的配置类
    - params: 查看指定配置类的参数说明
    - train: 执行训练，可以从配置文件或命令行参数创建配置

    属性:
        parser (argparse.ArgumentParser): 命令行参数解析器
        subparsers (argparse._SubParsersAction): 子命令解析器
        list_parser (argparse.ArgumentParser): 列出配置类的解析器
        params_parser (argparse.ArgumentParser): 查看参数说明的解析器
        train_parser (argparse.ArgumentParser): 执行训练的解析器
        configs (CompositeConfig): 解析后的配置对象
    """

    def __init__(self):
        """初始化配置解析器。

        创建命令行参数解析器和子命令解析器，并为每个子命令添加相应的参数。
        """
        self.parser = argparse.ArgumentParser(description="训练脚本")

        # 子命令解析器
        self.subparsers = self.parser.add_subparsers(dest="command", help="可用命令")

        # 列出可用配置类
        self.list_parser = self.subparsers.add_parser("list", help="列出可用的配置类")

        # 查看参数说明
        self.params_parser = self.subparsers.add_parser(
            "params", help="查看配置类的参数说明"
        )
        self.params_parser.add_argument(
            "--type",
            type=str,
            required=True,
            help="配置类型",
        )
        self.params_parser.add_argument(
            "--name",
            type=str,
            required=True,
            help="配置类名称",
        )

        # 训练命令
        self.train_parser = self.subparsers.add_parser("train", help="执行训练")

        # 动态获取可用的配置类型
        configs = ConfigRegistry.list_available_configs()
        for config_type in configs.keys():
            self.train_parser.add_argument(
                f"--{config_type}_name",
                type=str,
                help=f"{config_type}配置名称",
            )
        self.train_parser.add_argument(
            "--config",
            type=str,
            help="配置文件路径(.json或.yaml)",
        )
        self.train_parser.add_argument(
            "--output_dir",
            type=str,
            default=None,
            help="输出目录",
        )
        self.train_parser.add_argument(
            "--params",
            nargs="*",
            default=[],
            help="其他参数，格式：key=value",
        )

        # 初始化配置
        self.configs = None

    def __call__(self):
        """使ConfigParser实例可调用，返回解析后的配置。

        Returns:
            CompositeConfig: 解析后的配置对象，如果解析失败则返回None
        """
        return self.configs

    @staticmethod
    def parse_extra_params(params_list: list = None) -> Dict[str, Any]:
        """解析额外的参数列表。

        将形如 ["key1=value1", "key2=value2"] 的参数列表解析为字典。

        Args:
            params_list: 参数列表，格式为 ["key1=value1", "key2=value2"]

        Returns:
            Dict[str, Any]: 解析后的参数字典

        Raises:
            ValueError: 当参数格式错误时抛出

        示例:
            >>> params = ConfigParser.parse_extra_params(["hidden_size=768", "num_layers=12"])
            >>> print(params)
            {'hidden_size': '768', 'num_layers': '12'}
        """
        params = {}

        for param in params_list:
            try:
                key, value = param.split("=")
                params[key] = value
            except ValueError:
                raise ValueError(f"参数格式错误: {param}，应为key=value格式")

        return params

    @staticmethod
    def load_config(config_path: str) -> Dict[str, Any]:
        """从文件加载配置。

        支持从JSON或YAML文件加载配置，并将其转换为CompositeConfig对象。

        Args:
            config_path (str): 配置文件路径，支持.json、.yaml或.yml扩展名

        Returns:
            CompositeConfig: 配置对象，包含所有子配置

        Raises:
            ValueError: 当配置文件格式不支持或配置无效时抛出

        示例:
            >>> config = ConfigParser.load_config("config.json")
            >>> print(config.model.hidden_size)
            768
        """
        path = Path(config_path)
        if not path.exists():
            raise ValueError(f"配置文件不存在: {path}")

        # 使用ConfigHelper加载配置文件
        try:
            config = ConfigHelper.load(dict, config_path)
        except (ValueError, TypeError) as e:
            raise ValueError(f"配置文件加载失败: {str(e)}")

        if not isinstance(config, dict):
            raise ValueError("配置文件必须是一个字典")

        config_types = {}
        config_params = {}
        
        # 提取配置类型和参数
        for key, value in config.items():
            if key.endswith("_name") and isinstance(value, str):
                base_type = key[:-5]  # 去掉 _name 后缀
                config_types[base_type] = value
                # 获取对应的配置参数
                if base_type in config and isinstance(config[base_type], dict):
                    config_params[base_type] = config[base_type]
                elif base_type not in config:
                    config_params[base_type] = {}
                else:
                    raise ValueError(f"{base_type}必须是一个字典")
        
        # 使用通用方法创建配置对象
        return ConfigParser.create_configs_from_params(config_types, config_params)

    def parse_args(self, args=None) -> CompositeConfig:
        """解析命令行参数并执行相应的操作。

        支持以下命令：
        - list: 列出所有可用的配置类
        - params: 查看指定配置类的参数说明
        - train: 执行训练，可以从配置文件或命令行参数创建配置

        Args:
            args: 命令行参数列表，如果为None则从sys.argv获取

        Returns:
            CompositeConfig: 解析后的配置对象，如果是list或params命令则返回None

        Raises:
            ValueError: 当参数无效或配置无效时抛出

        示例:
            >>> parser = ConfigParser()
            >>> config = parser.parse_args(["train", "--model_name", "bert", "--params", "hidden_size=768"])
            >>> print(config.model.hidden_size)
            768
        """
        args = self.parser.parse_args(args)
        configs = None

        if args.command == "list":
            # 列出可用的配置类
            all_configs = ConfigRegistry.list_available_configs()
            print("\n可用的配置类:")
            for config_type, names in all_configs.items():
                print(f"\n{config_type.title()}配置类:")
                for name in names:
                    print(f"  - {name}")

        elif args.command == "params":
            # 显示参数说明
            try:
                params = ConfigRegistry.get_config_params(args.type, args.name)
                print(f"\n{args.type.title()}配置类 '{args.name}' 的参数说明:")
                for name, doc in params.items():
                    print(f"  {name}: {doc}")
            except ValueError as e:
                print(f"错误: {e}")
                return None

        elif args.command == "train":
            try:
                # 解析额外参数
                params = self.parse_extra_params(args.params)
                
                # 收集配置类型和参数
                config_types = {}
                config_params = {}
                
                if args.config:
                    # 从配置文件读取
                    path = Path(args.config)
                    if not path.exists():
                        raise ValueError(f"配置文件不存在: {path}")
                    
                    # 加载配置文件
                    config_data = ConfigHelper.load(dict, args.config)
                    if not isinstance(config_data, dict):
                        raise ValueError("配置文件必须是一个字典")
                    
                    # 提取配置类型和参数
                    for key, value in config_data.items():
                        if key.endswith("_name") and isinstance(value, str):
                            base_type = key[:-5]  # 去掉 _name 后缀
                            config_types[base_type] = value
                            # 获取对应的配置参数
                            if base_type in config_data and isinstance(config_data[base_type], dict):
                                config_params[base_type] = config_data[base_type]
                else:
                    # 从命令行参数收集配置类型
                    for config_type in ConfigRegistry.list_available_configs().keys():
                        name_arg = getattr(args, f"{config_type}_name")
                        if name_arg:
                            config_types[config_type] = name_arg
                
                # 验证并分配额外参数
                assigned_params = ConfigRegistry.validate_and_assign_params(
                    config_types, params, valid_missing=not bool(args.config)
                )
                
                # 合并参数：配置文件参数 + 额外参数
                for config_type in config_types:
                    if config_type not in config_params:
                        config_params[config_type] = {}
                    # 更新参数（额外参数会覆盖配置文件中的参数）
                    config_params[config_type].update(assigned_params.get(config_type, {}))
                
                # 使用通用方法创建配置对象
                configs = self.create_configs_from_params(config_types, config_params)
                
                # 设置输出目录（如果指定了）
                if hasattr(configs, "training") and args.output_dir:
                    configs.training.output_dir = args.output_dir

            except ValueError as e:
                print(f"错误: {e}")
                return None

        self.configs = configs
        return configs

    @staticmethod
    def create_configs_from_params(
        config_types: Dict[str, str], 
        config_params: Dict[str, Dict[str, Any]]
    ) -> CompositeConfig:
        """从配置类型和参数创建配置对象。

        Args:
            config_types: 配置类型和名称的映射，格式为 {config_type: config_name}
            config_params: 配置参数的映射，格式为 {config_type: {param_name: param_value}}

        Returns:
            CompositeConfig: 创建的复合配置对象

        Raises:
            ValueError: 当配置类不存在或缺少必需参数时抛出
        """
        configs = {}
        
        for config_type, name in config_types.items():
            config_cls = ConfigRegistry.get_config(config_type, name)
            if config_cls:
                # 获取该配置类型的参数
                params = config_params.get(config_type, {})
                
                # 检查必需参数
                missing_params = []
                for param_name in ConfigRegistry._get_required_params(config_cls):
                    if param_name not in params:
                        missing_params.append(f"{config_type}.{param_name}")
                if missing_params:
                    raise ValueError(
                        f"{config_type}缺少必需参数: {', '.join(missing_params)}"
                    )
                
                # 创建配置对象
                configs[config_type] = ConfigHelper.post_init(
                    config_cls(**params)
                )
                
                # 确保配置对象有正确的名称
                if not hasattr(configs[config_type], "name") or not configs[config_type].name:
                    configs[config_type].name = name
        
        return CompositeConfig(**configs)
