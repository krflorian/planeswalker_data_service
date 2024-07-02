from abc import ABC
from typing import Any, Tuple
from chromadb.api.models.Collection import Collection
from typing import Optional, List, Dict

from etl.database import ChromaDB, ETLMode


class Extractor(ABC):

    def __init__(self, db=ChromaDB, etl_mode: ETLMode = ETLMode.FULL):
        self.db = db
        self.etl_mode = etl_mode
        self.documents = []

    def get_data(self) -> Tuple[str | list, list]:
        """
        Get the raw and processed data by calling the get_data_raw and get_data_processed methods.
        """
        self.full_extract()
        self.transform_data()
        self.loader.upsert_documents_to_collection(self.documents)
        pass

    def full_extract(self) -> None:
        """
        Extract data from the data source, and save it as .txt or .json to the directory specified in self.path_data_raw
        """
        pass

    def delta_extract(self) -> None:
        """
        Extract data from the data source, and save it as .txt or .json to the directory specified in self.path_data_raw
        """
        pass

    def transform_data(self) -> None:
        """
        Load data from the directory specified in self.path_data_raw, transform the data, so that it is a list of json objects, and save them to the directory specified in self.path_data_processed.
        """
        pass
