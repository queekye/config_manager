import unittest
from pathlib import Path
import json
import yaml
from dataclasses import dataclass, field
from config_manager import ConfigRegistry, ConfigParser
import pytest


@ConfigRegistry.register("model", "test_model")
@dataclass
class ModelConfig:
    input_dim: int
    output_dim: int
    hidden_dims: list = field(default_factory=lambda: [256, 128])


@ConfigRegistry.register("training", "test_training")
@dataclass
class TrainingConfig:
    learning_rate: float
    batch_size: int
    epochs: int = 10
    output_dir: str = "./output"


class TestConfigParser(unittest.TestCase):
    def setUp(self):
        self.parser = ConfigParser()
        self.test_config_path = Path("test_config.yaml")

    def tearDown(self):
        if self.test_config_path.exists():
            self.test_config_path.unlink()

    def test_list_command(self):
        """测试list命令，验证是否能正确列出所有可用配置"""
        args = self.parser.parse_args(["list"])
        self.assertIsNone(args)

    def test_params_command(self):
        """测试params命令，验证是否能正确显示配置参数说明"""
        print("\n=== Parameters for test_model ===")
        args = self.parser.parse_args(
            ["params", "--type", "model", "--name", "test_model"]
        )
        self.assertIsNone(args)  # params命令直接打印信息，返回None
        print("==============================\n")

        print("\n=== Testing Invalid Config Type ===")
        # 测试无效的配置类型
        args = self.parser.parse_args(
            ["params", "--type", "invalid", "--name", "test_model"]
        )
        self.assertIsNone(args)
        print("================================\n")

    def test_train_command_with_config_file(self):
        """测试使用配置文件的train命令"""
        # 创建测试配置文件
        config_data = {
            "model_name": "test_model",
            "model": {"input_dim": 10, "output_dim": 2},
            "training_name": "test_training",
            "training": {"learning_rate": 0.001, "batch_size": 32},
        }
        with open(self.test_config_path, "w") as f:
            yaml.dump(config_data, f)

        args = self.parser.parse_args(["train", "--config", str(self.test_config_path)])
        self.assertIsNotNone(args)
        self.assertTrue(hasattr(args, "model"))
        self.assertTrue(hasattr(args, "training"))

        # 验证配置内容
        self.assertEqual(args.model.input_dim, 10)
        self.assertEqual(args.model.output_dim, 2)
        self.assertEqual(args.training.learning_rate, 0.001)
        self.assertEqual(args.training.batch_size, 32)

    def test_train_command_with_cli_params(self):
        """测试使用命令行参数的train命令"""
        args = self.parser.parse_args(
            [
                "train",
                "--model_name",
                "test_model",
                "--training_name",
                "test_training",
                "--params",
                "input_dim=10",
                "output_dim=2",
                "learning_rate=0.001",
                "batch_size=32",
            ]
        )

        self.assertIsNotNone(args)
        self.assertTrue(hasattr(args, "model"))
        self.assertTrue(hasattr(args, "training"))

        # 验证配置内容
        self.assertEqual(args.model.input_dim, 10)
        self.assertEqual(args.model.output_dim, 2)
        self.assertEqual(args.training.learning_rate, 0.001)
        self.assertEqual(args.training.batch_size, 32)

    def test_train_command_with_output_dir(self):
        """测试train命令的输出目录参数"""
        args = self.parser.parse_args(
            [
                "train",
                "--model_name",
                "test_model",
                "--training_name",
                "test_training",
                "--output_dir",
                "./custom_output",
                "--params",
                "input_dim=10",
                "output_dim=2",
                "learning_rate=0.001",
                "batch_size=32",
            ]
        )

        self.assertIsNotNone(args)
        self.assertEqual(args.training.output_dir, "./custom_output")

    def test_invalid_config_file(self):
        """测试无效的配置文件"""
        # 创建无效的配置文件
        with open(self.test_config_path, "w") as f:
            f.write("invalid: yaml: content:")

        with self.assertRaises(yaml.YAMLError):
            self.parser.parse_args(["train", "--config", str(self.test_config_path)])

    def test_invalid_params_format(self):
        """测试无效的参数格式"""
        args = self.parser.parse_args(
            [
                "train",
                "--model_name",
                "test_model",
                "--training_name",
                "test_training",
                "--params",
                "invalid_param",  # 缺少=号
            ]
        )

        self.assertIsNone(args)

    def test_params_override_config_file(self):
        """测试--params参数是否能覆盖配置文件中的参数"""
        # 创建测试配置文件
        config_data = {
            "model_name": "test_model",
            "model": {"input_dim": 10, "output_dim": 2, "hidden_dims": [256, 128]},
            "training_name": "test_training",
            "training": {"learning_rate": 0.001, "batch_size": 32, "epochs": 10},
        }
        with open(self.test_config_path, "w") as f:
            yaml.dump(config_data, f)

        # 同时指定--config和--params，params中的参数应该覆盖config文件中的参数
        args = self.parser.parse_args(
            [
                "train",
                "--config",
                str(self.test_config_path),
                "--params",
                "output_dim=5",  # 覆盖config中的output_dim
                "learning_rate=0.01",  # 覆盖config中的learning_rate
                "epochs=20",  # 覆盖config中的epochs
            ]
        )

        self.assertIsNotNone(args)
        self.assertTrue(hasattr(args, "model"))
        self.assertTrue(hasattr(args, "training"))

        # 验证未覆盖的参数保持原值
        self.assertEqual(args.model.input_dim, 10)
        self.assertEqual(args.training.batch_size, 32)

        # 验证被覆盖的参数是否成功更新
        self.assertEqual(args.model.output_dim, 5)  # 从2变为5
        self.assertEqual(args.training.learning_rate, 0.01)  # 从0.001变为0.01
        self.assertEqual(args.training.epochs, 20)  # 从10变为20
        
        # 保存配置并验证
        args.save(self.test_config_path)
        
        # 读取保存的配置文件并验证内容
        with open(self.test_config_path, "r") as f:
            saved_config = yaml.safe_load(f)
            
        # 验证关键参数是否正确保存
        self.assertEqual(saved_config["model"]["input_dim"], 10)
        self.assertEqual(saved_config["model"]["output_dim"], 5)
        self.assertEqual(saved_config["training"]["batch_size"], 32)
        self.assertEqual(saved_config["training"]["learning_rate"], 0.01)
        self.assertEqual(saved_config["training"]["epochs"], 20)


if __name__ == "__main__":
    unittest.main()
