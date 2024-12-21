# Import requests library
import requests
import urllib
import json
import time
from tqdm import tqdm
from pydantic import Field
from pathlib import Path
from mtg.logging import get_logger


from mtg.objects import Document
from .data_extractor import DataExtractor

logger = get_logger()

class RulesGuruExtractor(DataExtractor):
    api_url: str = "https://rulesguru.net/api/questions/"
    path_data_raw: Path = Path("../data/etl/raw/documents/rulesguru.json")
    path_data_processed: Path = Path("../data/etl/processed/documents/rulesguru.json")

    ids: list[str] = Field(default_factory=list)
    path_ids: Path = Path("../data/etl/raw/documents/ids.txt")

    def _get_ids(self):
        logger.info(f"fetching rulesguru ids")
        url = "https://rulesguru.org/getQuestionsList"

        # Define the JSON payload
        payload = {
            "settings": {
                "level": ["0", "1", "2", "3", "Corner Case"],
                "complexity": ["Simple", "Intermediate", "Complicated"],
                "legality": "All of Magic",
                "expansions": [],
                "playableOnly": True,
                "tags": ["Unsupported answers"],
                "tagsConjunc": "NOT",
                "rules": [],
                "rulesConjunc": "OR",
                "cards": [],
                "cardsConjunc": "OR",
                "cardDisplayFormat": "Image"
            }
        }

        try:
            # Send the POST request
            response = requests.post(url, headers={}, json=payload)

            # Check if the request was successful
            response.raise_for_status()

            # If the response contains JSON data, parse and return it
            data = response.json()
            return data


        except Exception as e:
            print(f"An error occurred: {e}")  # Other errors

    #def _get_ids(self):
    #    with open(self.path_ids) as f:
    #        ids = f.read().splitlines()
    #    self.ids = list(map(int, ids))

    def _get_query_params(self, id):
        query_params = {"id": id}

        query_params = json.dumps(query_params)
        query_params = urllib.parse.quote(query_params, safe="")

        return query_params

    def _get_params(self, count):
        query_params = {
            "count": count,         
            "level": ["0", "1", "2", "3", "Corner Case"],
            "complexity": ["Simple", "Intermediate", "Complicated"],
            "legality": "All of Magic",
            "expansions": [],
            "playableOnly": True,
            "tags": [],
            "tagsConjunc": "NOT",
            "rules": [],
            "rulesConjunc": "OR",
            "cards": [],
            "cardsConjunc": "OR",
        }
        query_params = json.dumps(query_params)
        query_params = urllib.parse.quote(query_params, safe="")

        return query_params

    def extract_data(self):
        self._get_ids()
        logger.info(f"downloading {len(self.ids)}rulesguru question")
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
                        "question": entry["question"]["questionSimple"],
                        "answer": entry["question"]["answerSimple"],
                        "complexity": entry["question"]["complexity"],
                        "includedCards": [
                            card["name"] for card in entry["question"]["includedCards"]
                        ],
                    },
                    keywords=entry["question"]["tags"],
                )
            )

        self._to_file(path=self.path_data_processed, data=self.data_processed)
