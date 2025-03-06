# Config Manager

一个灵活的配置注册和管理系统，用于简化项目中的配置管理。本项目提供了一个统一的配置注册机制，支持多种类型配置的管理，并具有参数验证、类型转换等功能。

## 特性

- 支持多种类型配置的注册和管理
- 提供参数类型自动转换功能（支持基本类型、列表和字典）
- 内置参数冲突检测，避免不同类型配置间的参数名冲突
- 支持配置组合，方便统一管理多个配置
- 提供命令行参数解析功能，支持从命令行覆盖配置
- 支持 JSON 和 YAML 格式配置文件的读写
- 自动进行参数类型验证和转换
- 支持配置参数的文档注释提取

## 安装

```bash
# 从源码安装
git clone https://github.com/yourusername/config_manager.git
cd config_manager
pip install -e .

# 或者直接安装
pip install config-manager
```

## 快速开始

### 基本使用

```python
from config_manager import ConfigRegistry
from dataclasses import dataclass

# 定义配置类
@ConfigRegistry.register("model", "mlp")
@dataclass
class MLPConfig:
    """MLP模型配置类
    
    Args:
        input_dim: 输入维度
        output_dim: 输出维度
        hidden_dims: 隐藏层维度列表
        dropout_rate: Dropout比率
        activation: 激活函数
        use_batch_norm: 是否使用批归一化
    """
    name: str = "mlp"
    input_dim: int = 10
    output_dim: int = 2
    hidden_dims: list = [256, 128]
    dropout_rate: float = 0.1
    activation: str = "relu"
    use_batch_norm: bool = True

# 获取配置类
config_cls = ConfigRegistry.get_config("model", "mlp")

# 创建配置实例
config = config_cls(
    input_dim=784,
    output_dim=10
)

# 查看配置参数说明
params = ConfigRegistry.get_config_params("model", "mlp")
print(params)
```

### 参数类型转换

系统支持多种类型的自动转换：

```python
from config_manager import ConfigRegistry, ConfigHelper
from dataclasses import dataclass

@ConfigRegistry.register("training", "default")
@dataclass
class TrainingConfig:
    """训练配置类
    
    Args:
        batch_size: 批次大小
        learning_rate: 学习率
        use_cuda: 是否使用GPU
        layer_sizes: 网络层大小列表
        optimizer_params: 优化器参数
    """
    name: str = "default"
    batch_size: int = 32
    learning_rate: float = 0.001
    use_cuda: bool = True  # 字符串 "true", "yes", "1" 会自动转换为 True
    layer_sizes: list = [512, 256]  # 字符串 "512,256" 会自动转换为 [512, 256]
    optimizer_params: dict = {"lr": 0.001}  # 字符串 '{"lr": 0.001}' 会被正确解析

# 创建配置并进行类型转换
config = TrainingConfig(
    batch_size="64",  # 字符串会自动转换为整数
    use_cuda="yes",   # 会自动转换为 True
    layer_sizes="128,64,32"  # 会自动转换为列表 [128, 64, 32]
)

# 执行类型转换
config = ConfigHelper.post_init(config)
print(config.batch_size, type(config.batch_size))  # 64 <class 'int'>
print(config.use_cuda, type(config.use_cuda))      # True <class 'bool'>
print(config.layer_sizes, type(config.layer_sizes))  # [128, 64, 32] <class 'list'>
```

### 配置组合

支持通过组合来管理多个配置：

```python
from config_manager import CompositeConfig, ConfigHelper

# 创建各个配置
model_config = MLPConfig(input_dim=784, output_dim=10)
training_config = TrainingConfig(batch_size=32, learning_rate=0.001)

# 使用组合配置
composite = CompositeConfig(
    model=model_config,
    training=training_config
)

# 访问组合配置
print(composite.model.input_dim)  # 784
print(composite.training.batch_size)  # 32
print(composite.model_name)  # "mlp"

# 保存完整配置
composite.save("experiment_config.json")  # 或 .yaml
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

### 命令行解析

支持通过命令行解析配置：

```python
from config_manager import ConfigParser

# 初始化解析器
parser = ConfigParser()

# 解析命令行参数
configs = parser.parse_args()

# 如果是训练命令，获取配置
if configs is None:
    return

if hasattr(configs, "model") and hasattr(configs, "training"):
    # 获取模型和训练配置
    model_config = configs.model
    train_config = configs.training
    
    print(f"模型配置: {model_config}")
    print(f"训练配置: {train_config}")
    
    # 这里可以根据配置构建模型和执行训练
    # ...

if __name__ == "__main__":
    main()
```

命令行使用示例：

```bash
# 列出所有可用配置
python train.py list

# 查看特定配置的参数说明
python train.py params --type model --name mlp

# 从配置文件加载并执行训练
python train.py train --config config.yaml

# 从命令行参数创建配置并执行训练
python train.py train --model_name mlp --training_name default --params "hidden_dims=[1024,512]" "batch_size=64"
```

## API 文档

### ConfigRegistry

配置注册中心，用于管理不同类型的配置类。

主要方法：
- `register(config_type, name)`: 注册配置类的装饰器
- `get_config(config_type, name)`: 获取指定类型和名称的配置类
- `list_available_configs()`: 列出所有可用的配置类
- `get_config_params(config_type, name)`: 获取指定配置类的参数说明
- `validate_and_assign_params(config_types, params, valid_missing)`: 验证并分配参数到相应的配置类

### ConfigParser

配置解析器，用于从命令行参数或配置文件解析配置。

主要方法：
- `parse_args(args)`: 解析命令行参数
- `load_config(config_path)`: 从文件加载配置
- `parse_extra_params(params_list)`: 解析额外的参数列表

### ConfigHelper

配置辅助工具，提供配置对象的序列化、反序列化和类型转换等功能。

主要方法：
- `to_dict(config_obj)`: 将配置对象转换为字典格式
- `save(config_obj, path)`: 将配置保存到文件
- `load(config_cls, path)`: 从文件加载配置
- `post_init(config_obj)`: 配置对象初始化后的处理函数，执行参数的自动类型转换和验证

### CompositeConfig

组合配置类，用于封装多个子配置，提供统一的访问接口。

主要方法：
- `__init__(**configs)`: 初始化组合配置类
- `__getattr__(name)`: 通过属性访问子配置
- `to_dict()`: 将配置对象转换为字典格式
- `save(path)`: 将配置保存到文件

## 实际应用示例

以下是一个完整的训练脚本示例，展示如何在实际项目中使用配置管理系统：

```python
from config_manager import ConfigRegistry, ConfigParser
from dataclasses import dataclass

# 定义配置类
@ConfigRegistry.register("model", "cnn")
@dataclass
class CNNConfig:
    """CNN模型配置
    
    Args:
        in_channels: 输入通道数
        num_classes: 类别数量
        kernel_size: 卷积核大小
    """
    name: str = "cnn"
    in_channels: int = 3
    num_classes: int = 10
    kernel_size: int = 3

@ConfigRegistry.register("training", "default")
@dataclass
class TrainingConfig:
    """训练配置
    
    Args:
        batch_size: 批次大小
        learning_rate: 学习率
        epochs: 训练轮数
        output_dir: 输出目录
    """
    name: str = "default"
    batch_size: int = 32
    learning_rate: float = 0.001
    epochs: int = 10
    output_dir: str = "./output"

def main():
    # 解析命令行参数
    parser = ConfigParser()
    configs = parser.parse_args()
    
    if configs is None:
        return
    
    if hasattr(configs, "model") and hasattr(configs, "training"):
        # 获取模型和训练配置
        model_config = configs.model
        train_config = configs.training
        
        print(f"模型配置: {model_config}")
        print(f"训练配置: {train_config}")
        
        # 这里可以根据配置构建模型和执行训练
        # ...

if __name__ == "__main__":
    main()
```

## 许可证

本项目采用 MIT 许可证。详见 LICENSE 文件。