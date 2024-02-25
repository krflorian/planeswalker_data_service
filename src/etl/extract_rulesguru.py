# Import requests library
import requests
import urllib
import json
import time
from tqdm import tqdm
from pydantic import BaseModel, Field
from pathlib import Path
from src.objects import Document


class RulesGuru(BaseModel):
    # Define the API endpoint
    path_raw_data: Path = Path("../data/etl/raw/documents/rulesguru.json")
    path_processed_data: Path = Path("../data/etl/processed/documents/rulesguru.json")
    data: list[dict] = Field(default_factory=list)
    documents: list[Document] = Field(default_factory=list)
    api_url: str = "https://rulesguru.net/api/questions/"
    ids: list[str] = Field(default_factory=list)
    path_ids: Path = Path("ids.txt")

    def post_model_load(self):
        self.get_ids()

    def load(self):
        if Path(self.path_raw_data).is_file():
            self.from_file()
            # TODO delta load
            # self.data.append(self.delta_load())
        else:
            self.full_load()
            self.to_file()
        pass

    def get_max_id_raw(self):
        max_id_raw = max(self.data, key=lambda x: x["id"])
        return max_id_raw

    def get_max_id_source(self):
        pass

    def full_load(self):
        print("TODO")
        pass

    def delta_load(self):
        # max_id_source =
        if get_max_id_raw() < get_max_id_source():
            self.delta_load()

    def get_ids(self):
        with open(self.path_ids) as f:
            ids = f.read().splitlines()
        self.ids = list(map(int, ids))

    def _get_query_params(self, id):
        query_params = {"id": id}

        query_params = json.dumps(query_params)
        query_params = urllib.parse.quote(query_params, safe="")

        return query_params

    def full_load(self):
        for id in tqdm(self.ids):
            try:
                time.sleep(2)
                response = requests.get(
                    api_url + "?json=" + self._get_query_params(id), timeout=3600
                )

                if response.status_code == 200:
                    data = response.json()
                    question_answer = {"question": data["questions"][0]}
                    self.questions.append(question_answer)

                else:
                    # Print the status code and the reason
                    print(response.status_code, response.reason)

            except:
                pass

        return

    def process_data(self):
        for entry in self.data:
            dict = {
                "name": f"RulesGuru.net Question-ID: {entry['question']['id']}",
                "text": f"Question: {entry['question']['questionSimple']} Answer: {entry['question']['answerSimple']}",
                "url": entry["question"]["url"],
                "metadata": {
                    "origin": "RulesGuru.net",
                    "level": entry["question"]["level"],
                    "complexity": entry["question"]["complexity"],
                    "includedCards": [
                        card["name"] for card in entry["question"]["includedCards"]
                    ],
                },
                "keywords": entry["question"]["tags"],
            }
            self.documents.append(dict)
        self.to_file(self.documents, self.path_processed_data)

    def from_file(self):
        with open(self.path_raw_data, "r", encoding="utf-8") as file:
            self.data = json.load(file)

    def to_file(self, data, path):
        if not data:
            data = self.data
        if not path:
            path = self.path_raw_data
        # Open the file in write mode
        with open(path, "w", encoding="utf-8") as file:
            # Dump the dictionary as JSON to the file
            json.dump(data, file)


# %%

from src.objects import Document

# %%
from pathlib import Path

rg = RulesGuru(
    path_raw_data=Path("../data/etl/raw/documents/rulesguru.json"),
    path_processed_data=Path("../data/etl/processed/documents/rulesguru.json"),
)

# %%
rg.from_file()
# %%
rg.data

# %%
rg.process_data()
