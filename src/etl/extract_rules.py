import requests
import random
import json
import re

from pathlib import Path
from datetime import datetime

from pydantic import BaseModel, Field
from sentence_transformers import SentenceTransformer

from src.objects import Document
from src.vector_db import VectorDB


class Rules(BaseModel):
    db_name: str = "rules_db_gte"
    path_processed_documents: Path = Path("../data/etl/processed/documents/")
    path_artifacts: Path = Path("../data/artifacts")
    path_raw_data: Path = Path("../data/etl/raw/documents/rules.txt")
    path_processed_data: Path = Path("../data/etl/processed/documents/rules.json")
    data: list[dict] = Field(default_factory=list)
    documents: list[Document] = Field(default_factory=list)
    api_url: str = (
        "https://media.wizards.com/2024/downloads/MagicCompRules%2020240206.txt"
    )

    def post_model_load(self):
        #self.extract_data()
        #self.transform_data()
        #self.load_data()
        pass

    def extract_data(self):
        try:
            response = requests.get(self.api_url)
            response.raise_for_status()  # Raise an exception if the request was unsuccessful
            with open(self.path_raw_data, "w") as file:
                file.write(response.text)
            self.data = response.text
            print(f"File downloaded successfully and saved at {self.path_raw_data}")
        except requests.RequestException as e:
            print("Error downloading")

    def transform_data(self):
        now = datetime.now()
        # split the text by the word 'Credits' and take the second part starting with the rules
        text = self.data.split("Credits", 1)[1]
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
                            self.documents.append(
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
                                self.documents.append(
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
            self.documents.append(
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

        doc = random.choice(self.documents)
        print("___________________")
        print(f"Processed {len(self.documents)} self.documents like this:")
        for key, value in doc.model_dump().items():
            print(key, ": ", value)
        print("___________________")

        print(
            "docs with keywords: ", len([doc for doc in self.documents if doc.keywords])
        )

    def load_data(self):
        # load documents

        for file in self.path_processed_documents.iterdir():
            if file.suffix != ".json":
                continue
            print(f"loading data from {file.name}")
            with file.open("r", encoding="utf-8") as infile:
                data = json.load(infile)
            self.documents.extend([Document(**d) for d in data])
        print(f"loaded {len(self.documents)} documents")

        # load model
        model = SentenceTransformer(
            "thenlper/gte-large"
        )  # sentence-transformers/all-MiniLM-L6-v2

        rules_db = VectorDB(
            texts=[doc.text for doc in self.documents],
            data=self.documents,
            model=model,
        )

        # save rules db
        rules_db.dump(self.path_artifacts / f"{self.db_name}.p")

    def load_data_raw(self):
        if Path(self.path_raw_data).is_file():
            self.from_file()
            # TODO delta load
            # self.data.append(self.delta_load())
        else:
            self.extract_data()
            self.to_file()

    def from_file(self, path=None):
        if path is None:
            path = self.path_raw_data
        with open(self.path_raw_data, "r", encoding="utf-8") as file:
            self.data = json.load(file)

    def to_file(self, data, path):
        if data is None:
            data = self.data
        if path is None:
            path = self.path_raw_data
        # Open the file in write mode
        with open(path, "w", encoding="utf-8") as file:
            # Dump the dictionary as JSON to the file
            json.dump(data, file)
