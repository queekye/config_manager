import pytest
from dataclasses import dataclass
from config_manager import ConfigRegistry, CompositeConfig


@ConfigRegistry.register("model", "test")
@dataclass
class ModelConfig:
    input_dim: int
    output_dim: int


@ConfigRegistry.register("training", "test")
@dataclass
class TrainingConfig:
    batch_size: int
    learning_rate: float
    
@pytest.fixture
def model_config():
    return ModelConfig(input_dim=10, output_dim=20)

@pytest.fixture
def training_config():
    return TrainingConfig(batch_size=32, learning_rate=0.001)

def test_composite_config_creation(model_config, training_config):
    # 测试创建组合配置
    composite = CompositeConfig(
        model=model_config,
        training=training_config
    )
    
    assert composite.model == model_config
    assert composite.training == training_config

def test_composite_config_access(model_config, training_config):
    # 测试访问组合配置的属性
    composite = CompositeConfig(model=model_config, training=training_config)
    
    assert composite.model.input_dim == 10
    assert composite.training.batch_size == 32
    
    # 测试访问不存在的属性
    with pytest.raises(AttributeError):
        _ = composite.nonexistent

def test_composite_config_to_dict(model_config, training_config):
    # 测试配置转换为字典
    composite = CompositeConfig(model=model_config, training=training_config)
    config_dict = composite.to_dict()
    
    assert isinstance(config_dict, dict)
    assert "model" in config_dict
    assert "training" in config_dict
    assert config_dict["model"]["input_dim"] == 10
    assert config_dict["training"]["batch_size"] == 32