from pydantic import BaseModel, Field
from typing import Tuple, Any
from pathlib import Path
import json

from src.objects import Document


class DataExtractor(BaseModel):
    api_url: str
    path_data_raw: Path
    path_data_processed: Path
    data_raw: Any = ""
    data_processed: list = Field(default_factory=list)
    data_processed_json: list = Field(default_factory=list)

    def extract_data(self) -> None:
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
        if self.data_raw:
            pass
        else:
            self.get_data_raw()

        if self.data_processed:
            pass
        else:
            self.get_data_processed()

        return self.data_raw, self.data_processed

    def get_data_raw(self) -> str | list:
        """
        Load the raw data into class variable "data_raw".
        """

        if self.path_data_raw.is_file():
            self.data_raw = self._from_file(self.path_data_raw)
        else:
            self.extract_data()
            self.data_raw = self._from_file(self.path_data_raw)
        return self.data_raw

    def get_data_processed(self) -> list:
        """
        Load the raw data into class variable "data_processed".
        """
        if self.path_data_processed.is_file():
            self.data_processed = self._from_file(self.path_data_processed)
        elif self.path_data_raw.is_file():
            self.transform_data()
            self.data_processed = self._from_file(self.path_data_processed)
        return self.data_processed

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
            print(f"opening a file with filetype {path.suffix} is not supported")

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

        else:
            print(f"opening a file with filetype {path.suffix} is not supported")
