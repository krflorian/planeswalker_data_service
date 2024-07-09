import yaml
from pathlib import Path


def load_config(config_file: Path) -> dict:
    if not isinstance(config_file, Path):
        config_file = Path(config_file)

    with config_file.open("r") as infile:
        config = yaml.load(infile, Loader=yaml.FullLoader)

    return config
