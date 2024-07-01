from pydantic import BaseModel, Field
from typing import Any, Tuple
from chromadb.api.models.Collection import Collection
from .loader import Loader
from typing import Optional, List, Dict


class Extractor(BaseModel):
    collection_name: str = Field(None, description="Collection Name for ChromaDB")
    config: Dict = Field(None, description="Config for ChromaDB")
    documents: Optional[List] = Field(None, description="Collection object from ChromaDB")
    loader: Optional[Loader] = Field(None, description="Collection object from ChromaDB")

    def model_post_init(self, __context: Any) -> None:
        self.loader = Loader(collection_name=self.collection_name, config=self.config)

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




