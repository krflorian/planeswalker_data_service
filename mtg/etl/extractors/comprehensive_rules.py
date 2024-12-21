#%%
import requests
import json
import re
import logging

from pathlib import Path
from datetime import datetime

from mtg.objects import Document
from .data_extractor import DataExtractor
#%%

class ComprehensiveRulesExtractor(DataExtractor):
    api_url: str = (
        "https://magic.wizards.com/en/rules"
    )

    keywords_url: str = "https://api.scryfall.com/catalog/keyword-abilities"
    keywords: list = []
    path_data_keywords: Path = Path("../data/etl/raw/documents/keyword_list.txt")
    path_data_raw: Path = Path("../data/etl/raw/documents/rules.txt")
    path_data_processed: Path = Path("../data/etl/processed/documents/rules.json")

    def get_keywords(self):
        response = requests.get(self.keywords_url)
        response.raise_for_status()  # Check for request errors
        self.keywords = json.loads(response.text)['data']
        self._to_file(path=self.path_data_keywords, data=str(self.keywords))
        logging.info(f"{len(self.keywords)} Keywords extracted and saved to {self.path_data_keywords}")
 
    
    def get_cr_url(self):
        try:
            # Send a GET request to the URL
            response = requests.get(self.api_url)
            response.raise_for_status()  # Check for request errors

            # Define a regex pattern to match the exact .txt file URL
            # This pattern looks for the specific structure and filename
            pattern = r'https://media\.wizards\.com/\d{4}/downloads/MagicCompRules\s\d{8}\.txt'
            match = re.search(pattern, response.text)

            if match:
                return match.group(0)
            else:
                print("The specific .txt file link was not found on the page.")
                return None

        except requests.exceptions.RequestException as e:
            print(f"An error occurred: {e}")
            return None

    def extract_data(self):
        try:
            self.get_keywords()
            cr_url = self.get_cr_url()
            response = requests.get(cr_url)
            response.raise_for_status()  # Raise an exception if the request was unsuccessful
            self._to_file(self.path_data_raw, response.text)
            logging.info(
                f"downloaded comprehensive rules data, saving in {self.path_data_raw}"
            )
        except requests.RequestException as e:
            print("Error downloading")

    def transform_data(self):
        now = datetime.now()
        text = self._from_file(self.path_data_raw)
        # split the text by the word 'Credits' and take the second part starting with the rules
        text = text.split("Credits", 1)[1]
        # split the text by the word 'Glossary' and take the first part as rules
        rules = text.split("Glossary", 1)[0]
        # split the text by the word 'Glossary' and take the second part as text
        text = text.split("Glossary", 1)[1]
        # split the text by the word 'Credits' and take the first part as glossary_entries
        glossary_entries = text.split("Credits", 1)[0]

        #with open(Path("../data/etl/raw/documents/keyword_list.json"), "r") as infile:
        #    keywords = json.load(infile)
        # chunk rules
        rule_pattern = r"(\n\d{3}\.\d+.)"
        chapter_pattern = r"(\n\d{3}\. .*)"
        chapters = re.split(chapter_pattern, rules)
        for text in chapters[1:]:
            # chapter
            if re.match(chapter_pattern, text):
                chapter = text
                chapter = chapter.replace("\n", "").strip()
            else:
                # rules
                rules = re.split(rule_pattern, text)
                rules = [r for r in rules if r not in ["\n", ""]]
                subchapter = None
                for rule_text in rules:
                    # rule id
                    if re.match(rule_pattern, rule_text):
                        rule_id = rule_text
                        rule_id = rule_id.replace("\n", "")
                    # rule text
                    else:
                        if len(rule_text.split()) // 2 <= 1:  # max 1 token
                            subchapter = rule_text.strip()
                        else:
                            examples = []
                            if "Example:" in rule_text:
                                rule_text = rule_text.split("Example:")
                                examples = rule_text[1:]
                                rule_text = rule_text[0]

                            # TODO keywords
                            self.data_processed.append(
                                Document(
                                    name=f"Comprehensive Rules: {chapter} {subchapter if subchapter is not None else ''}: {rule_id}",
                                    text=rule_text.strip(),
                                    url=f"https://yawgatog.com/resources/magic-rules/#R{rule_id.replace('.', '')}",
                                    metadata={
                                        "timestamp": str(now),
                                        "origin": "Magic the Gathering: Comprehensive Rules",
                                        "filename": "MagicCompRules.txt",
                                        "chapter": chapter,
                                        "subchapter": (
                                            subchapter if subchapter is not None else ""
                                        ),
                                        "rule_id": rule_id,
                                    },
                                    keywords=[
                                        keyword
                                        for keyword in self.keywords
                                        if keyword.lower() in rule_text.lower()
                                    ],
                                )
                            )
                            for example in examples:
                                self.data_processed.append(
                                    Document(
                                        name=f"Example for Rule {subchapter if subchapter is not None else ''}: {rule_id}",
                                        text=example.strip(),
                                        url=f"https://yawgatog.com/resources/magic-rules/#R{rule_id.replace('.', '')}",
                                        metadata={
                                            "timestamp": str(now),
                                            "origin": "Magic the Gathering: Comprehensive Rules",
                                            "filename": "MagicCompRules.txt",
                                            "chapter": chapter,
                                            "subchapter": (
                                                subchapter
                                                if subchapter is not None
                                                else ""
                                            ),
                                            "rule_id": rule_id,
                                        },
                                        keywords=[
                                            keyword
                                            for keyword in self.keywords
                                            if keyword.lower() in rule_text.lower()
                                        ],
                                    )
                                )

        # chunk glossary
        glossary_entries = glossary_entries.split("\n\n")
        glossary_entries = [x for x in glossary_entries if (x not in ["", "\n"])]
        for glossary_text in glossary_entries:
            entry_id = glossary_text.split("\n")[0]
            self.data_processed.append(
                Document(
                    name=f"Glossary: {entry_id}",
                    text=glossary_text.strip(),
                    url="https://blogs.magicjudges.org/rules/cr-glossary/",
                    metadata={
                        "origin": "Magic the Gathering: Comprehensive Rules",
                        "timestamp": str(now),
                        "filename": "MagicCompRules.txt",
                        "chapter": "Glossary",
                    },
                    keywords=[
                        keyword
                        for keyword in self.keywords
                        if keyword.lower() in rule_text.lower()
                    ],
                )
            )

        self._to_file(self.path_data_processed, self.data_processed)
        logging.info(
            f"extracted comprehensive rules data {len(self.data_processed)} documents, saving in {self.path_data_raw}"
        )
