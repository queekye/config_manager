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
class MLPConfig:
    name: str
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
class TrainingConfig:
    # 字符串会自动转换为布尔值
    use_cuda: bool = True  # "true", "yes", "1" 都会转换为 True
    
    # 字符串会自动转换为列表
    layer_sizes: list = [512, 256]  # "512,256" 会转换为 [512, 256]
    
    # 字符串会自动转换为字典
    optimizer_params: dict = {"lr": 0.001}  # '{"lr": 0.001}' 会被正确解析
```

### 配置继承和组合

支持通过继承和组合来复用和管理配置：

```python
# 通过继承扩展配置
@ConfigRegistry.register("model", "enhanced_mlp")
@dataclass
class EnhancedMLPConfig(MLPConfig):
    use_residual: bool = True
    num_layers: int = 3

# 使用组合配置管理多个相关配置
from config_manager import CompositeConfig

# 使用组合配置
model_config = MLPConfig(name="mnist_model", input_dim=784, output_dim=10)
training_config = TrainingConfig(batch_size=32, learning_rate=0.001)

composite = CompositeConfig(
    model=model_config,
    training=training_config
)

# 访问组合配置
assert composite.model.input_dim == 784
assert composite.training.batch_size == 32

# 创建组合配置
config = ExperimentConfig(
    model=MLPConfig(input_dim=784, output_dim=10),
    training=TrainingConfig(batch_size=32, learning_rate=0.001)
)

# 保存完整配置
config.save("experiment_config.yaml")
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

### 参数验证和约束

支持在配置类中添加参数验证和约束：

```python
from dataclasses import dataclass, field
from typing import List, Optional
from config_manager import ConfigRegistry, BaseConfig

@ConfigRegistry.register("training", "advanced")
@dataclass
class AdvancedTrainingConfig:
    name: str
    learning_rate: float = field(
        default=0.001,
        metadata={"help": "初始学习率", "range": [0.0001, 0.1]}
    )
    batch_size: int = field(
        default=32,
        metadata={"help": "训练批次大小", "range": [1, 512]}
    )
    optimizer: str = field(
        default="adam",
        metadata={"choices": ["adam", "sgd", "rmsprop"]}
    )
    
    def __post_init__(self):
        if self.learning_rate < 0.0001 or self.learning_rate > 0.1:
            raise ValueError("Learning rate must be between 0.0001 and 0.1")
        if self.batch_size < 1 or self.batch_size > 512:
            raise ValueError("Batch size must be between 1 and 512")
```

### 实际应用示例

以下是一个完整的训练脚本示例，展示如何在实际项目中使用配置管理系统：

```python
from config_manager import ConfigRegistry, ConfigParser
from torch import nn, optim

def main():
    # 解析命令行参数
    parser = ConfigParser()
    args = parser.parse_args()
    
    # 获取模型和训练配置
    model_config = args.model
    train_config = args.training
    
    # 构建模型
    model = build_model(model_config)
    
    # 配置优化器
    optimizer = getattr(optim, train_config.optimizer)(
        model.parameters(),
        lr=train_config.learning_rate
    )
    
    # 配置学习率调度器
    if train_config.scheduler:
        scheduler = get_scheduler(optimizer, train_config)
    
    # 训练循环
    for epoch in range(train_config.epochs):
        train_epoch(model, optimizer, train_config)
        if scheduler:
            scheduler.step()
        
        # 保存检查点
        if epoch % train_config.save_interval == 0:
            save_checkpoint(model, optimizer, epoch, train_config.output_dir)

if __name__ == "__main__":
    main()
```

## API 文档

### ConfigRegistry

配置注册中心，用于管理不同类型的配置类。主要提供以下方法：

- `register(config_type: str, name: str) -> Callable`
  - 功能：注册配置类的装饰器
  - 参数：
    - config_type: 配置类型（如 "model", "training"）
    - name: 配置名称
  - 返回：装饰器函数
  - 示例：
    ```python
    @ConfigRegistry.register("model", "resnet")
    @dataclass
    class ResNetConfig:
        layers: int = 50
        pretrained: bool = True
    ```

- `get_config(config_type: str, name: str) -> Type[BaseConfig]`
  - 功能：获取指定类型和名称的配置类
  - 参数：
    - config_type: 配置类型
    - name: 配置名称
  - 返回：配置类
  - 异常：ConfigNotFoundError（配置不存在时）

- `list_available_configs() -> Dict[str, List[str]]`
  - 功能：列出所有可用的配置类
  - 返回：字典，键为配置类型，值为该类型下的配置名称列表

- `get_config_params(config_type: str, name: str) -> Dict[str, Dict]`
  - 功能：获取指定配置类的参数说明
  - 参数：
    - config_type: 配置类型
    - name: 配置名称
  - 返回：参数说明字典
  - 异常：ConfigNotFoundError（配置不存在时）

### CompositeConfig

组合配置类，用于封装和管理多个子配置。主要提供以下方法：

- `__init__(**configs)`
  - 功能：初始化组合配置
  - 参数：configs - 关键字参数，包含多个子配置实例
  - 示例：
    ```python
    composite = CompositeConfig(
        model=ModelConfig(type="resnet"),
        training=TrainingConfig(epochs=100)
    )
    ```

- `__getattr__(name: str) -> BaseConfig`
  - 功能：通过属性访问子配置
  - 参数：name - 子配置名称
  - 返回：子配置实例
  - 异常：AttributeError（子配置不存在时）

- `to_dict() -> Dict`
  - 功能：将组合配置转换为字典
  - 返回：包含所有子配置信息的字典

- `save(path: str) -> None`
  - 功能：将组合配置保存到文件
  - 参数：path - 保存路径（支持 .yaml 或 .json）
  - 异常：IOError（文件操作失败时）


### ConfigParser

配置解析器，提供命令行参数解析和配置文件加载功能。主要提供以下方法：

- `__init__(description: str = None)`
  - 功能：初始化配置解析器
  - 参数：description - 命令行工具描述

- `add_config_type(config_type: str) -> None`
  - 功能：添加配置类型
  - 参数：config_type - 配置类型名称

- `parse_args(args: List[str] = None) -> Namespace`
  - 功能：解析命令行参数
  - 参数：args - 命令行参数列表（可选）
  - 返回：解析后的参数对象

- `load_config(path: str) -> Dict`
  - 功能：加载配置文件
  - 参数：path - 配置文件路径
  - 返回：配置字典
  - 异常：ConfigFileError（文件格式错误）

使用示例：
```python
# 初始化解析器
parser = ConfigParser()

# 解析参数
args = parser.parse_args()

# 获取特定配置
model_config = config["model"]
training_config = config["training"]
```

命令行参数支持：
```bash
# 训练命令
python train.py train \
    --model_name resnet \
    --training_name default \
    --config config.yaml \
    --params "learning_rate=0.01" "batch_size=64"

# 查看配置信息
python train.py list  # 列出所有配置
python train.py params --type model --name resnet  # 查看特定配置参数
```

## 许可证

本项目采用 MIT 许可证。详见 LICENSE 文件。