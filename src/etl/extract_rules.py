from pathlib import Path
from datetime import datetime
import re
import random
import json

from src.objects import Document

COMPREHENSIVE_RULES_URL = "https://magic.wizards.com/en/rules"


def load_rules(rules_file: Path = Path("../data/etl/raw/documents/MagicCompRules.txt")) -> str:
    with open(rules_file, "r", encoding="utf-8") as f:
        text = f.read()
    return text


def extract_rules(text: str, keywords: list[str]) -> list[str]:
    now = datetime.now()
    # split the text by the word 'Credits' and take the second part starting with the rules
    text = text.split("Credits", 1)[1]
    # split the text by the word 'Glossary' and take the first part as rules
    rules = text.split("Glossary", 1)[0]
    # split the text by the word 'Glossary' and take the second part as text
    text = text.split("Glossary", 1)[1]
    # split the text by the word 'Credits' and take the first part as glossary_entries
    glossary_entries = text.split("Credits", 1)[0]

    # chunk rules
    documents = []

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
                        documents.append(
                            Document(
                                name=f"Comprehensive Rules: {chapter} {subchapter if subchapter is not None else ''}: {rule_id}",
                                text=rule_text.strip(),
                                url=f'https://blogs.magicjudges.org/rules/cr{chapter}/',
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
                            documents.append(
                                Document(
                                    name=f"Example for Rule {subchapter if subchapter is not None else ''}: {rule_id}",
                                    text=example.strip(),
                                    url=COMPREHENSIVE_RULES_URL,
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

    # chunk glossary
    glossary_entries = glossary_entries.split("\n\n")
    glossary_entries = [x for x in glossary_entries if (x not in ["", "\n"])]
    for glossary_text in glossary_entries:
        entry_id = glossary_text.split("\n")[0]
        documents.append(
            Document(
                name=f"Glossary: {entry_id}",
                text=glossary_text.strip(),
                url=COMPREHENSIVE_RULES_URL,
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

    doc = random.choice(documents)
    print("___________________")
    print(f"Processed {len(documents)} Documents like this:")
    for key, value in doc.model_dump().items():
        print(key, ": ", value)
    print("___________________")

    print("docs with keywords: ", len([doc for doc in documents if doc.keywords]))
    return documents


if __name__ == "__main__":
    DATA_PATH = Path("../data/")
    ETL_PATH = DATA_PATH / "etl"

    # load
    # comprehensive rulebook from COMPREHENSIVE_RULES_URL as txt document
    text = load_rules(rules_file=ETL_PATH / "raw/MagicCompRules.txt")

    with open(ETL_PATH / "raw/keyword_list.json", "r") as infile:
        keywords = json.load(infile)

    # extract
    documents = extract_rules(text=text, keywords=keywords)

    # save documents
    document_jsons = [doc.model_dump() for doc in documents]
    with open(
        ETL_PATH / "processed/documents/comprehensive_rules.json",
        "w",
        encoding="utf-8",
    ) as outfile:
        json.dump(document_jsons, outfile, ensure_ascii=False)
