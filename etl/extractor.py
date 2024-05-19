from pydantic import BaseModel, Field
from typing import Tuple, Any
from pathlib import Path
import json
from chromadb.api.models.Collection import Collection
from typing import Union, Optional, List, Any
from etl import Loader


class Extractor(BaseModel):
    documents: Optional[List] = Field(None, description="Collection object from ChromaDB")
    collection_name: str = Field('crRulesss', description="Name of the collection in ChromaDB")
    collection: Optional[Collection] = Field(None, description="Collection object from ChromaDB")



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

    def get_data(self) -> Tuple[str | list, list]:
        """
        Get the raw and processed data by calling the get_data_raw and get_data_processed methods.
        """
        self.collection = Loader(collection_name=self.collection_name)

        if self.collection.count() == 0:
            self.transform_data(self.full_extract())
        else:
            self.transform_data(self.delta_extract())

    def _from_file(self, path: Path) -> str | list:
        """
        Load data from a file with the given path. Supports .txt and .json file types.
        """
        if path.suffix == ".txt":
            with open(path, "r", encoding="utf-8") as file:
                data = file.read()
            return data
        elif path.suffix == ".json":
            with open(path, "r", encoding="utf-8") as file:
                data = json.load(file)
            return data
        else:
            logger.error(f"opening a file with filetype {path.suffix} is not supported")

    def _to_file(self, path: Path, data: str | list[Document]) -> None:
        """
        Save data to a file with the given path. Supports .txt and .json file types.
        """
        if path.suffix == ".txt":
            with open(path, "w", encoding="utf-8") as file:
                file.write(data)
        elif path.suffix == ".json":
            json_data = []
            for doc in data:
                json_data.append(doc.model_dump())

            with open(path, "w", encoding="utf-8") as outfile:
                json.dump(json_data, outfile)

            logger.info(
                f"{self.__class__.__name__} saving {len(data)} documents in {path}"
            )
        else:
            logger.error(f"opening a file with filetype {path.suffix} is not supported")



