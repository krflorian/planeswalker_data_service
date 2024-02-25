import requests
import random
import json
import re

from pathlib import Path
from datetime import datetime

from src.objects import Document
from src.etl.extract import DataExtractor


class Rules(DataExtractor):
    api_url: str = "https://media.wizards.com/2024/downloads/MagicCompRules%2020240206.txt"
    path_data_raw: Path = Path("../data/etl/raw/documents/rules.txt")
    path_data_processed: Path = Path("../data/etl/processed/documents/rules.json")


    def post_model_load(self):
        pass

    def extract_data(self):
        try:
            response = requests.get(self.api_url)
            response.raise_for_status()  # Raise an exception if the request was unsuccessful
            with open(self.path_data_raw, "w") as file:
                file.write(response.text)
            self.data_raw = response.text
            print(f"File downloaded successfully and saved at {self.path_data_raw}")
        except requests.RequestException as e:
            print("Error downloading")

    def transform_data(self):
        now = datetime.now()
        # split the text by the word 'Credits' and take the second part starting with the rules
        text = self.data_raw.split("Credits", 1)[1]
        # split the text by the word 'Glossary' and take the first part as rules
        rules = text.split("Glossary", 1)[0]
        # split the text by the word 'Glossary' and take the second part as text
        text = text.split("Glossary", 1)[1]
        # split the text by the word 'Credits' and take the first part as glossary_entries
        glossary_entries = text.split("Credits", 1)[0]

        with open(Path("../data/etl/raw/documents/keyword_list.json"), "r") as infile:
            keywords = json.load(infile)
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
                                    url=f"https://blogs.magicjudges.org/rules/cr{chapter}/",
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
                                        for keyword in keywords
                                        if keyword.lower() in rule_text.lower()
                                    ],
                                )
                            )
                            for example in examples:
                                self.data_processed.append(
                                    Document(
                                        name=f"Example for Rule {subchapter if subchapter is not None else ''}: {rule_id}",
                                        text=example.strip(),
                                        url=f"https://blogs.magicjudges.org/rules/cr{chapter}/",
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
                                            for keyword in keywords
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
                        for keyword in keywords
                        if keyword.lower() in rule_text.lower()
                    ],
                )
            )

        doc = random.choice(self.data_processed)
        print("___________________")
        print(f"Processed {len(self.data_processed)} self.documents like this:")
        for key, value in doc.model_dump().items():
            print(key, ": ", value)
        print("___________________")

        print(
            "docs with keywords: ", len([doc for doc in self.data_processed if doc.keywords])
        )
