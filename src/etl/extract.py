from pydantic import BaseModel, Field

from pathlib import Path
import json


class DataExtractor(BaseModel):
    api_url: str
    path_data_raw: Path
    path_data_processed: Path
    data_raw: list = Field(default_factory=list)
    data_processed: list = Field(default_factory=list)

    def extract_data(self):
        """
        Extract data from the data source.
        """
        pass

    def transform_data(self):
        """
        Transform the extracted data.
        This function should always take as the contents of the file at "path_data_raw" and save the outcome to "path_data_processed"
        """
        pass

    def get_data_raw(self):
        """
        Load the raw data into class variable "data_raw".
        """
        if self.data_raw:
            pass
        elif self.path_data_raw.is_file():
            self.data_raw = self._from_file(self.path_data_raw)
        else:
            self.extract_data()
            self.data_raw = self._from_file(self.path_data_raw)
        return self.data_raw

    def get_data_processed(self):
        """
        Load the raw data into class variable "data_processed".
        """
        if self.data_processed:
            pass
        elif self.path_data_processed.is_file():
            self.data_processed = self._from_file(self.path_data_processed)
        elif self.path_data_raw.is_file():
            self.transform_data()
            self.data_processed = self._from_file(self.path_data_processed)
        else:
            self.extract_data()
            self.transform_data()
            self.data_processed = self._from_file(self.path_data_processed)
        return self.data_processed

    def _from_file(self, path):
        """
        Load data from a JSON file.
        This method takes a file path as an argument, opens the file in read mode with utf-8 encoding, and uses the json module to load the data from the file.
        """
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
        return data

    def _to_file(self, path, data):
        """
        Save data to a JSON file.
        This method takes a data object and a file path as arguments, opens the file in write mode with utf-8 encoding.
        """
        with open(path, "w", encoding="utf-8") as file:
            json.dump(data, file)
