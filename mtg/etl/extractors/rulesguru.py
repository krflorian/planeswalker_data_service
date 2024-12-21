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
    path_data_raw: Path = Path("../data/etl/raw/documents/rulesguru.txt")
    path_data_processed: Path = Path("../data/etl/processed/documents/rulesguru.json")

    ids: list[str] = Field(default_factory=list)
    path_ids: Path = Path("../data/etl/raw/documents/ids.txt")
    batch_size: int = 100

    def _get_ids(self):
        """
        Fetches the list of question IDs from the RulesGuru API.
        
        Returns:
            list: A list of ordered question IDs.
        """
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
            # Parse and return JSON data
            data = response.json()
            if isinstance(data, list):
                logger.info(f"Retrieved {len(data)} question IDs.")
                self.ids = data
                return data
            else:
                logger.error("Unexpected data format received from getQuestionsList.")
                return []
        except Exception as e:
            logger.error(f"An error occurred while fetching IDs: {e}")
            return []


    def _get_query_params(self, count: int, previous_id: int):
        """
        Constructs the query parameters for the API request.
        
        Args:
            count (int): Number of questions to fetch.
            previous_id (int): The ID after which to fetch the next set of questions.
        
        Returns:
            str: URL-encoded JSON string of query parameters.
        """
        query_params = {
            "count": count,    
            "previousId": previous_id,     
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
        query_json = json.dumps(query_params)
        query_encoded = urllib.parse.quote(query_json, safe="")
        return query_encoded

    def extract_data(self):
        self._get_ids()
        total_ids = len(self.ids)
        current_index = 1

        self.data_raw = []

        while current_index < total_ids:
            # Determine the batch of IDs to fetch
            batch_ids = self.ids[current_index:current_index + self.batch_size]
            if not batch_ids:
                break

            if current_index == 1:
                # Assuming 0 is a valid previousId that fetches from the start
                previous_id = 1
            else:
                previous_id = self.ids[current_index - 1]

            params = self._get_query_params(count=self.batch_size, previous_id=previous_id)

            try:
                # Send GET request to fetch the batch
                logger.info(f"Fetching batch of IDs from {self.api_url}?json={params}")
                response = requests.get(self.api_url + "?json=" + params, timeout=3600)
                response.raise_for_status()
                questions = response.json()["questions"]
                self.data_raw.extend(questions)
                
                #yield questions
                fetched_count = len(questions)
                logger.info(f"Fetched {fetched_count} questions starting after ID {previous_id}.")
                    #pbar.update(fetched_count)
                    
                    # Update the current_index
                current_index += fetched_count

                    # If fewer questions are returned than requested, assume wrap-around or end
                if fetched_count < self.batch_size:
                    logger.info("Fetched fewer questions than requested. Assuming end of list.")
                    break

            except Exception as e:
                logger.error(f"An error occurred while fetching questions: {e}")
                logger.info("Retrying after delay...")
                break

        self._to_file(path=self.path_data_raw, data=str(self.data_raw))

    def transform_data(self):
        for entry in self.data_raw:
            self.data_processed.append(
                Document(
                    name=f"RulesGuru.net Question-ID: {entry['id']}",
                    text=f"Question: {entry['questionSimple']} Answer: {entry['answerSimple']}",
                    url=entry["url"],
                    metadata={
                        "origin": "RulesGuru.net",
                        "level": entry["level"],
                        "question": entry["questionSimple"],
                        "answer": entry["answerSimple"],
                        "complexity": entry["complexity"],
                        "includedCards": [
                            card["name"] for card in entry["includedCards"]
                        ],
                    },
                    keywords=entry["tags"],
                )
            )

        self._to_file(path=self.path_data_processed, data=self.data_processed)
