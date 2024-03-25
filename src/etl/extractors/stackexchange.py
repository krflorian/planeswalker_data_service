# %%
import json
import re
from stackapi import StackAPI
from datetime import datetime
from pathlib import Path
from pydantic import Field
import logging

from .data_extractor import DataExtractor
from src.objects import Document


class StackExchangeExtractor(DataExtractor):
    api_url: str = "boardgames"
    path_data_raw: Path = Path("../data/etl/raw/documents/stackoverflow.json")
    path_data_processed: Path = Path(
        "../data/etl/processed/documents/stackoverflow.json"
    )

    page_size: int = Field(default=50)
    max_year: int = Field(default=2025)
    min_year: int = Field(default=2010)
    tags: list[str] = [
        "mtg-stack",
        "mtg-commander",
        "magic-the-gathering",
        "mtg-priority",
    ]

    def extract_data(self) -> None:

        api = StackAPI(self.api_url)
        api.page_size = self.page_size
        api.max_pages = 1

        logging.info(
            f"downloading data from stackoverflow years {self.min_year}-{self.max_year}"
        )
        processed_documents, seen_questions = [], set()
        for year in range(self.min_year, self.max_year):
            for tag in self.tags:
                questions = api.fetch(
                    "questions",
                    tagged=tag,
                    sort="votes",
                    order="desc",
                    filter="withbody",
                    fromdate=datetime(year=year, month=1, day=1),
                    todate=datetime(year=year + 1, month=1, day=1),
                )

                questions_with_answers = []
                for item in questions["items"]:
                    if (
                        item["is_answered"]
                        and ("accepted_answer_id" in item)
                        and (item["score"] > 0)
                    ):
                        if item["question_id"] not in seen_questions:
                            questions_with_answers.append(item)
                            seen_questions.add(item["question_id"])

                if questions_with_answers:
                    ids = [
                        item["accepted_answer_id"] for item in questions_with_answers
                    ]
                    answers = api.fetch(
                        "answers",
                        ids=ids,
                        tagged="magic-the-gathering",
                        filter="withbody",
                    )
                    anwer_id_2_answer = {
                        answer["answer_id"]: answer for answer in answers["items"]
                    }

                    for item in questions_with_answers:
                        item["answer"] = anwer_id_2_answer[item["accepted_answer_id"]]
                        processed_documents.append(item)

        logging.info(
            f"downloaded {len(processed_documents)} documents from stackoverflow saving in {self.path_data_raw}"
        )

        # self._to_file(self.path_data_raw, processed_documents)
        self.data_raw = processed_documents
        with open(self.path_data_raw, "w", encoding="utf-8") as outfile:
            json.dump(processed_documents, outfile, ensure_ascii=False)

    def transform_data(self) -> None:

        if not self.data_raw:
            self.data_raw = self._from_file(self.path_data_raw)

        logging.info(f"Transforming {len(self.data_raw)} items from Stackexchange")
        documents = []
        for item in self.data_raw:
            title = item["title"]
            question = clean_html_tags(item["body"])
            answer = clean_html_tags(item["answer"]["body"])
            documents.append(
                Document(
                    name=f"Stackexchange Question {item['question_id']}",
                    text="\n".join(
                        ["Question: " + title, question, "Answer: " + answer]
                    ),
                    url=item["link"],
                    metadata={
                        "question": question,
                        "answer": answer,
                        "title": title,
                        "tags": item["tags"],
                        "score": str(item["score"]),
                    },
                )
            )

        print(f"saving processed Stackexchange data in {self.path_data_processed}")
        self._to_file(self.path_data_processed, data=documents)


def clean_html_tags(text):
    for match in re.finditer(pattern=r"<[^>]+>", string=text):
        html_tag = match.group()
        if "img src" in html_tag:
            card_name = (
                re.search(r'alt="([^"]*)"', html_tag).group().replace("alt=", "")
            )
            # print(card_name)
            text = text.replace(html_tag, card_name)
        else:
            text = text.replace(html_tag, "")
    return text
