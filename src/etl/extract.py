from pydantic import BaseModel

from pathlib import Path
import json

class DataExtractor(BaseModel):
    path_data_raw: Path
    path_data_processed: Path
    data_raw: list
    data_processed: list
    api_url: str


    def post_model_load(self):
        #self.extract_data()
        #self.transform_data()
        pass

    def extract_data(self):
        """
        Extract data from the data source.
        """
        pass


    def transform_data(self):
        """
        Transform the extracted data.
        """
        pass


    def load_data_raw(self):
        """
        Load the raw data into class variable "data_raw".
        """
        self.data_raw = self.from_file(self.path_data_raw)
        

    def load_data_processed(self):
        """
        Load the raw data into class variable "data_processed".
        """
        self.data_processed = self.from_file(self.path_data_processed)
        

    def from_file(self, path):
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
        return data


    def to_file(self, data=None, path=None):
        with open(path, "w", encoding="utf-8") as file:
            # Dump the dictionary as JSON to the file
            json.dump(data, file)




    