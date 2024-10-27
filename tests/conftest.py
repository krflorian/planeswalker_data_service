import pytest
from pathlib import Path
from sentence_transformers import SentenceTransformer


@pytest.fixture(scope="session")
def model():
    model = SentenceTransformer("thenlper/gte-large")
    return model
