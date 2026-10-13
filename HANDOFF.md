# 项目交接

## 当前情况

这是通用 dataclass 配置组件的公开主线。PyPI 发行名为
`modern-config-manager`，Python 导入名为 `config_manager`。注册、参数冲突
检查、显式类型转换、JSON/YAML 保存与组合配置 CLI 已实现；它不执行模型
训练。现有 MIT LICENSE、Git 历史、v0.3.0/v0.3.1/v0.3.2 标签和发行版保留。

## 环境及运行

使用 Python 3.8+ 的独立虚拟环境；安装会下载 PyYAML，测试另需 pytest。
仓库 setup.py 仍保留原来的更低 Python 版本声明；当前维护验证环境见下文，
更低版本尚未重新验证。无模型、数据集、个人目录或账号资源要求。

```bash
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -e . pytest
python -m pytest -q
python examples/quickstart.py list
python examples/quickstart.py params --type model --name mlp
python examples/quickstart.py train --config examples/config.yaml
python examples/quickstart.py train --model_name mlp --training_name default --params 'hidden_dims=[64,32]' batch_size=4
```

示例只打印组合配置。项目使用者需要自行接入训练或应用入口。字段可变默认值
必须使用 `field(default_factory=...)`；指定 `List[int]` 才对列表元素执行
整数转换。直接构造 dataclass 不会自动调用 `ConfigHelper.post_init`。

## 已知边界及未来计划

2026-10-13 维护增加可运行示例和独立进程的 CLI 验证；验证源码安装、原有测试、
示例 YAML/参数覆盖、可变默认值隔离及 wheel 安装。没有重新发布 PyPI，
没有变更原标签，PyPI 项目配置/Trusted Publisher 的管理权限未登录确认。
错误 CLI 参数会打印错误并返回 None，当前不是严格非零退出协议。

科研仓中的相似配置实现先保留为带来源的历史组件。统一前应比较扩展行为，
不要用本库覆盖专用配置器。后续可改进错误退出协议、复杂/嵌套类型验证、
补低版本/多平台测试及安装 wheel 的 CI；做这些 API 改动时另升版本并发布。
不要把个人配置、密钥、训练结果或模型权重提交到通用库。
