import argparse
from pathlib import Path
import json
import yaml
from typing import Tuple, Dict, Any

from .registry import ConfigRegistry
from .composite import CompositeConfig


class ConfigParser:
    def __init__(self):
        self.parser = argparse.ArgumentParser(description="训练脚本")
        
        # 子命令解析器
        self.subparsers = self.parser.add_subparsers(dest="command", help="可用命令")
        
        # 列出可用配置类
        self.list_parser = self.subparsers.add_parser("list", help="列出可用的配置类")
        
        # 查看参数说明
        self.params_parser = self.subparsers.add_parser("params", help="查看配置类的参数说明")
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
                required=True,
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
        
        # 在初始化时自动执行main方法
        # self.configs = self._main()

    def __call__(self):
        """使ConfigParser实例可调用，返回解析后的配置"""
        return self.configs
    
    @staticmethod
    def parse_extra_params(params_list: list = None) -> Dict[str, Any]:
        """解析额外的参数列表
        
        Args:
            params_list: 参数列表，格式为 ["key1=value1", "key2=value2"]
            
        Returns:
            解析后的参数字典
            
        Raises:
            ValueError: 当参数格式错误时抛出
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
        """从文件加载配置
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            配置对象字典，键为配置类型
            
        Raises:
            ValueError: 当配置文件格式不支持或配置无效时抛出
        """
        path = Path(config_path)
        if not path.exists():
            raise ValueError(f"配置文件不存在: {path}")
            
        if path.suffix == '.json':
            with open(path, 'r', encoding='utf-8') as f:
                try:
                    config = json.load(f)
                except json.JSONDecodeError as e:
                    raise ValueError(f"JSON格式错误: {e}")
        elif path.suffix in {'.yaml', '.yml'}:
            with open(path, 'r', encoding='utf-8') as f:
                try:
                    config = yaml.safe_load(f)
                except yaml.YAMLError as e:
                    raise ValueError(f"YAML格式错误: {e}")
        else:
            raise ValueError(f"不支持的配置文件格式: {path.suffix}")
        
        if not isinstance(config, dict):
            raise ValueError("配置文件必须是一个字典")
        
        configs = {}
        # 遍历所有配置类型
        for config_type, config_data in config.items():
            if config_type.endswith("_name"):
                # 获取基本配置类型（去掉_name后缀）
                base_type = config_type[:-5]
                if not isinstance(config_data, str):
                    raise ValueError(f"{config_type}的值必须是字符串")
                config_name = config_data
                config_cls = ConfigRegistry.get_config(base_type, config_name)
                
                if config_cls:
                    # 获取对应的配置数据
                    config_data = config.get(f"{base_type}", {})
                    if not isinstance(config_data, dict):
                        raise ValueError(f"{base_type}必须是一个字典")
                    if 'name' not in config_data:
                        config_data['name'] = config[config_type]
                    configs[base_type] = config_cls(**config_data)
        
        return CompositeConfig(**configs)
    
    def parse_args(self, args=None):
        """主解析函数"""
        args = self.parser.parse_args(args)
        configs = None
        
        if args.command == "list":
            # 列出可用的配置类
            configs = ConfigRegistry.list_available_configs()
            print("\n可用的配置类:")
            for config_type, names in configs.items():
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

                # 从配置文件或命令行参数创建配置
                if args.config:
                    configs = self.load_config(args.config)
                else:
                    # 收集所有配置类型和名称
                    config_types = {}
                    for config_type in ConfigRegistry.list_available_configs().keys():
                        name_arg = getattr(args, f"{config_type}_name")
                        if name_arg:
                            config_types[config_type] = name_arg
                    
                    # 验证并分配参数
                    assigned_params = ConfigRegistry.validate_and_assign_params(
                        config_types,
                        params
                    )
                    
                    # 创建配置对象
                    configs = {}
                    for config_type, name in config_types.items():
                        config_cls = ConfigRegistry.get_config(config_type, name)
                        if config_cls:
                            configs[config_type] = config_cls(**assigned_params[config_type])
                    
                    # 设置输出目录
                    if "training" in configs and args.output_dir:
                        configs["training"].output_dir = args.output_dir
                    
                    # 将配置字典转换为CompositeConfig对象
                    configs = CompositeConfig(**configs)
            except (ValueError, TypeError) as e:
                print(f"错误: {e}")
                return None
        
        return configs