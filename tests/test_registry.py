import unittest
from dataclasses import dataclass, field
from typing import List
from config_manager import ConfigRegistry
import pytest


# 测试用的配置类
@ConfigRegistry.register("model", "test_registry_model")
@dataclass
class ModelConfig:
    input_dim: int
    output_dim: int
    hidden_dims: List[int] = field(default_factory=lambda: [256, 128])
    name: str = "test_model"


@ConfigRegistry.register("training", "test_registry_training")
@dataclass
class TrainingConfig:
    learning_rate: float
    batch_size: int
    epochs: int = 10
    name: str = "test_training"

class TestConfigRegistry(unittest.TestCase):
    def test_register_and_get_config(self):
        """测试配置类的注册和获取"""
        # 测试获取已注册的配置类
        model_config = ConfigRegistry.get_config("model", "test_registry_model")
        self.assertIsNotNone(model_config)
        self.assertEqual(model_config.__name__, "ModelConfig")
        
        # 测试获取不存在的配置类
        invalid_config = ConfigRegistry.get_config("invalid", "invalid")
        self.assertIsNone(invalid_config)
    
    def test_list_available_configs(self):
        """测试列出可用配置类"""
        configs = ConfigRegistry.list_available_configs()
        self.assertIsInstance(configs, dict)
        self.assertIn("model", configs)
        self.assertIn("training", configs)
        self.assertIn("test_registry_model", configs["model"])
        self.assertIn("test_registry_training", configs["training"])
    
    def test_get_config_params(self):
        """测试获取配置参数说明"""
        # 测试获取有效配置的参数
        params = ConfigRegistry.get_config_params("model", "test_registry_model")
        self.assertIsInstance(params, dict)
        self.assertIn("input_dim", params)
        self.assertIn("output_dim", params)
        
        # 测试获取无效配置的参数
        with self.assertRaises(ValueError):
            ConfigRegistry.get_config_params("invalid", "invalid")
    
    def test_validate_and_assign_params(self):
        """测试参数验证和分配"""
        # 测试有效参数
        config_types = {
            "model": "test_registry_model",
            "training": "test_registry_training"
        }
        params = {
            "input_dim": 10,
            "output_dim": 2,
            "learning_rate": 0.001,
            "batch_size": 32
        }
        
        assigned_params = ConfigRegistry.validate_and_assign_params(config_types, params, valid_missing=True)
        self.assertIsInstance(assigned_params, dict)
        self.assertIn("model", assigned_params)
        self.assertIn("training", assigned_params)
        
        # 验证参数分配是否正确
        self.assertEqual(assigned_params["model"]["input_dim"], 10)
        self.assertEqual(assigned_params["training"]["learning_rate"], 0.001)
        
        # 测试缺少必需参数
        invalid_params = {"input_dim": 10}  # 缺少output_dim和其他必需参数
        with self.assertRaises(ValueError):
            assigned_params = ConfigRegistry.validate_and_assign_params(config_types, invalid_params, valid_missing=True)
        # 测试未知参数
        invalid_params = {"unknown_param": 42, **params}
        with self.assertRaises(ValueError):
            assigned_params = ConfigRegistry.validate_and_assign_params(config_types, invalid_params, valid_missing=True)
    
    def test_param_conflicts(self):
        """测试参数冲突检查"""
        # 尝试注册具有冲突参数的配置类
        with self.assertRaises(ValueError):
            @ConfigRegistry.register("optimizer", "test_optimizer")
            @dataclass
            class ConflictConfig:
                # input_dim 与 ModelConfig 冲突
                input_dim: int
                learning_rate: float

if __name__ == "__main__":
    unittest.main()