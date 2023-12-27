import yaml
from pathlib import Path


def load_config(config_file: Path) -> dict:
    with config_file.open("r") as infile:
        config = yaml.load(infile, Loader=yaml.FullLoader)

    return config
