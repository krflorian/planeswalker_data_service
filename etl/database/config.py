import os
import yaml
from typing import Literal, Union, Optional
from pathlib import Path

import logging
from pydantic import BaseModel, Field


class ChromaConfig(BaseModel):
    host: str = Field(default="localhost")
    port: int = Field(default=8000)
    embedding_model: str = Field(default="thenlper/gte-large")
    embedding_device: Literal["cpu", "gpu"] = Field(default="cpu")
    collection_name_documents: str = Field(default="documents")
    collection_name_cards: str = Field(default="cards")

    @classmethod
    def load_config(cls, filepath: Optional[Union[Path, str]] = None):
        """
        Load configurations from the config.yml file if it exists. If not, load from environment variables.
        If the variables are not defined in either, use the default values.
        """

        if filepath is not None:
            config = cls.load_from_file(filepath)
            return config
        else:
            return cls.load_from_env()

    @classmethod
    def load_from_file(cls, filepath):
        """Load configuration from the YAML file."""
        if not isinstance(filepath, Path):
            filepath = Path(filepath)

        try:
            with filepath.open("r") as file:
                config = yaml.safe_load(file)
                chroma_config = config.get("CHROMA")
                if chroma_config is None:
                    raise ValueError(
                        f"Please add CHROMA section to config: {str(filepath)}"
                    )
                return cls(**chroma_config)
        except yaml.YAMLError as e:
            logging.error(e, exc_info=True)
        except Exception as e:
            logging.error(e, exc_info=True)

    @classmethod
    def load_from_env(cls):
        """Load configuration from the environment variables."""
        return cls(
            host=os.getenv("CHROMA_HOST"),
            port=os.getenv("CHROMA_PORT"),
            embedding_model=os.getenv("CHROMA_EMBEDDING_MODEL"),
            embedding_device=os.getenv("CHROMA_EMBEDDING_DEVICE"),
            etl_mode=os.getenv("CHROMA_ETL_MODE"),
        )


if __name__ == "__main__":
    config = ChromaConfig.load_config("configs/config.yaml")
    print(config)
