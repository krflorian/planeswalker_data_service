import pytest
from pathlib import Path
from sentence_transformers import SentenceTransformer

from src.util import load_config


@pytest.fixture(scope="session")
def model():
    model = SentenceTransformer("thenlper/gte-large")
    return model


@pytest.fixture(scope="session")
def config():
    config = load_config(Path("configs/config.yaml"))
    return config
