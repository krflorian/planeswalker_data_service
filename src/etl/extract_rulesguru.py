# Import requests library
import requests
import urllib
import json
import time
from tqdm import tqdm
from pydantic import BaseModel, Field
from pathlib import Path
from src.objects import Document
from src.etl.extract import DataExtractor


class RulesGuru(DataExtractor):
    api_url: str = "https://rulesguru.net/api/questions/"
    path_data_raw: Path = Path("../data/etl/raw/documents/rulesguru.json")
    path_data_processed: Path = Path("../data/etl/processed/documents/rulesguru.json")

    ids: list[str] = Field(default_factory=list)
    path_ids: Path = Path("../data/etl/raw/documents/ids.txt")

    def _get_ids(self):
        with open(self.path_ids) as f:
            ids = f.read().splitlines()
        self.ids = list(map(int, ids))

    def _get_query_params(self, id):
        query_params = {"id": id}

        query_params = json.dumps(query_params)
        query_params = urllib.parse.quote(query_params, safe="")

        return query_params

    def extract_data(self):
        self._get_ids()
        for id in tqdm(self.ids):
            try:
                time.sleep(2)
                response = requests.get(
                    self.api_url + "?json=" + self._get_query_params(id), timeout=3600
                )

                if response.status_code == 200:
                    data = response.json()
                    question_answer = {"question": data["questions"][0]}
                    self.data_raw.append(question_answer)

                else:
                    # Print the status code and the reason
                    print(response.status_code, response.reason)

            except:
                pass

        return

    def transform_data(self):
        for entry in self.data_raw:
            self.data_processed.append(
                Document(
                    name=f"RulesGuru.net Question-ID: {entry['question']['id']}",
                    text=f"Question: {entry['question']['questionSimple']} Answer: {entry['question']['answerSimple']}",
                    url=entry["question"]["url"],
                    metadata={
                        "origin": "RulesGuru.net",
                        "level": entry["question"]["level"],
                        "complexity": entry["question"]["complexity"],
                        "includedCards": [
                            card["name"] for card in entry["question"]["includedCards"]
                        ],
                    },
                    keywords=entry["question"]["tags"],
                )   
            )
        
        self._to_json(self.data_processed)    
        self._to_file(self.path_data_processed, self.data_processed_json)
