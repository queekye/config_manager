# Config Manager

一个灵活的配置注册和管理系统，用于简化深度学习项目中的配置管理。本项目提供了一个统一的配置注册机制，支持多种类型配置的管理，并具有参数验证、类型转换等功能。

## 特性

- 支持多种类型配置的注册和管理
- 提供参数类型自动转换功能（支持基本类型、列表和字典）
- 内置参数冲突检测，避免不同类型配置间的参数名冲突
- 支持配置继承和组合，方便复用配置
- 提供命令行参数解析功能，支持从命令行覆盖配置
- 支持 JSON 和 YAML 格式配置文件的读写
- 自动进行参数类型验证和转换
- 支持配置参数的文档注释

## 安装

```bash
pip install modern-config-manager
```

## 快速开始

### 基本使用

```python
from config_manager import ConfigRegistry, BaseConfig
from dataclasses import dataclass

# 定义配置类
@ConfigRegistry.register("model", "mlp")
@dataclass
class MLPConfig(BaseConfig):
    input_dim: int
    output_dim: int
    hidden_dims: list = [256, 128]
    dropout_rate: float = 0.1
    activation: str = "relu"
    use_batch_norm: bool = True

# 获取配置类
config_cls = ConfigRegistry.get_config("model", "mlp")

# 创建配置实例
config = config_cls(
    name="mlp_model",
    input_dim=10,
    output_dim=2
)

# 保存配置
config.save("config.yaml")

# 加载配置
loaded_config = MLPConfig.load("config.yaml")
```

### 参数类型转换

系统支持多种类型的自动转换：

```python
@ConfigRegistry.register("training", "default")
@dataclass
class TrainingConfig(BaseConfig):
    # 字符串会自动转换为布尔值
    use_cuda: bool = True  # "true", "yes", "1" 都会转换为 True
    
    # 字符串会自动转换为列表
    layer_sizes: list = [512, 256]  # "512,256" 会转换为 [512, 256]
    
    # 字符串会自动转换为字典
    optimizer_params: dict = {"lr": 0.001}  # '{"lr": 0.001}' 会被正确解析
```

### 配置继承和组合

支持通过继承复用配置：

```python
@ConfigRegistry.register("model", "enhanced_mlp")
@dataclass
class EnhancedMLPConfig(MLPConfig):
    use_residual: bool = True
    num_layers: int = 3
```

### 配置文件格式

支持 YAML 和 JSON 格式的配置文件。配置文件结构示例：

```yaml
# 配置类型和名称
model_name: mlp
training_name: default

# 模型配置
model:
  input_dim: 784
  output_dim: 10
  hidden_dims: [512, 256]
  dropout_rate: 0.2

# 训练配置
training:
  batch_size: 128
  learning_rate: 0.001
  epochs: 100
  output_dir: "./output"
```

## API 文档

### ConfigRegistry

配置注册中心，用于管理不同类型的配置类。

- `register(config_type: str, name: str)`: 注册配置类的装饰器
- `get_config(config_type: str, name: str)`: 获取指定类型和名称的配置类
- `list_available_configs()`: 列出所有可用的配置类
- `get_config_params(config_type: str, name: str)`: 获取指定配置类的参数说明

### BaseConfig

所有配置类的基类，提供基本功能。

- `to_dict()`: 将配置对象转换为字典格式
- `save(path: str)`: 将配置保存到文件（支持 .json, .yaml, .yml）
- `load(path: str)`: 从文件加载配置

### CompositeConfig

组合配置类，用于封装和管理多个子配置。

- `__init__(**configs)`: 初始化组合配置，支持传入多个子配置
- `__getattr__(name: str)`: 通过属性访问子配置（如 `config.model`）
- `to_dict()`: 将组合配置转换为字典，包含所有子配置信息
- `save(path: str)`: 将组合配置保存到文件

### 配置解析器

提供命令行参数解析和配置文件加载功能。

主要功能：
- 支持命令行参数解析
- 支持从JSON/YAML文件加载配置
- 提供配置验证和参数分配
- 支持查看可用配置和参数说明

命令行使用示例：
```bash
# 列出所有可用配置
python train.py list

# 查看特定配置的参数说明
python train.py params --type model --name mlp

# 使用配置文件训练
python train.py train --model_name mlp --training_name default --config config.yaml

# 通过命令行参数覆盖配置
python train.py train --model_name mlp --training_name default --params "learning_rate=0.01" "batch_size=32"

# 指定输出目录
python train.py train --model_name mlp --training_name default --output_dir "./output"
```

## 许可证

本项目采用 MIT 许可证。详见 LICENSE 文件。