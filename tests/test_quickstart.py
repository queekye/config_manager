"""Exercise the documented example in fresh processes to isolate registries."""
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def run_example(*args):
    return subprocess.run([sys.executable, str(ROOT / "examples/quickstart.py"), *args],
                          cwd=ROOT, capture_output=True, text=True, check=True).stdout


def test_documented_listing_and_parameter_help():
    assert "mlp" in run_example("list")
    assert "Input features" in run_example("params", "--type", "model", "--name", "mlp")


def test_yaml_example_and_cli_override():
    actual = json.loads(run_example("train", "--config", "examples/config.yaml"))
    assert actual["model"]["input_dim"] == 784
    assert actual["model"]["hidden_dims"] == [64, 32]
    actual = json.loads(run_example("train", "--config", "examples/config.yaml",
                                    "--params", "batch_size=7", "use_cuda=yes"))
    assert actual["training"]["batch_size"] == 7
    assert actual["training"]["use_cuda"] is True


def test_cli_list_conversion_and_independent_mutable_defaults():
    actual = json.loads(run_example("train", "--model_name", "mlp", "--training_name", "default",
                                    "--params", "hidden_dims=[16,8]", "batch_size=2"))
    assert actual["model"]["hidden_dims"] == [16, 8]
    assert actual["training"]["batch_size"] == 2
    code = """import runpy
ns = runpy.run_path('examples/quickstart.py')
first = ns['ModelConfig']()
second = ns['ModelConfig']()
first.hidden_dims.append(1)
assert second.hidden_dims == [256, 128]
"""
    subprocess.run([sys.executable, "-c", code], cwd=ROOT, check=True)
