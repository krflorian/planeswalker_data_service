import yaml
from pathlib import Path
import json


def load_config(config_file: Path) -> dict:
    if not isinstance(config_file, Path):
        config_file = Path(config_file)

    with config_file.open("r") as infile:
        config = yaml.load(infile, Loader=yaml.FullLoader)

    return config


def read_json_file(file_path: Path):
    with file_path.open("r", encoding="utf-8") as file:
        return json.load(file)
