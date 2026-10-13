"""Runnable configuration example; no model training or external resources."""
from dataclasses import dataclass, field
import json
from typing import List

from config_manager import ConfigParser, ConfigRegistry


@ConfigRegistry.register("model", "mlp")
@dataclass
class ModelConfig:
    name: str = "mlp"
    input_dim: int = field(default=10, metadata={"help": "Input features"})
    output_dim: int = 2
    hidden_dims: List[int] = field(default_factory=lambda: [256, 128])
    dropout_rate: float = 0.1


@ConfigRegistry.register("training", "default")
@dataclass
class TrainingConfig:
    name: str = "default"
    batch_size: int = field(default=32, metadata={"help": "Batch size"})
    learning_rate: float = 0.001
    use_cuda: bool = False
    output_dir: str = "./output"


def main():
    configs = ConfigParser().parse_args()
    if configs is not None:
        print(json.dumps(configs.to_dict(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
