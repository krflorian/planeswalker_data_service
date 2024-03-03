# %%
import json
from stackapi import StackAPI
from datetime import datetime
from pathlib import Path
from pydantic import Field

from .data_extractor import DataExtractor
from src.objects import Document


class StackExchangeExtractor(DataExtractor):
    api_url: str = "boardgames"
    path_data_raw: Path = Path("../data/etl/raw/documents/stackoverflow.json")
    path_data_processed: Path = Path(
        "../data/etl/processed/documents/stackoverflow.json"
    )

    _api: StackAPI = StackAPI(api_url)
    _page_size: int = Field(default=50)
    _max_year: int = Field(default=2025)
    _min_year: int = Field(default=2010)
    _tags: list[str] = ["mtg-stack", "mtg-commander", "magic-the-gathering"]

    def model_post_init(self, *args, **kwargs) -> None:
        self._api.page_size = self._page_size
        self._api.max_pages = 1

    def extract_data(self) -> None:

        print(
            f"downloading data from stackoverflow years {self._min_year}-{self._max_year}"
        )
        processed_documents = []
        for year in range(self._min_year, self._max_year):
            for tag in self._tags:
                questions = self._api.fetch(
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
                        questions_with_answers.append(item)

                if questions_with_answers:
                    ids = [
                        item["accepted_answer_id"] for item in questions_with_answers
                    ]
                    answers = self._api.fetch(
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

        print(
            f"downloaded {len(processed_documents)} documents from stackoverflow saving in {self.path_data_raw}"
        )

        # self._to_file(self.path_data_raw, processed_documents)
        self.data_raw = processed_documents
        with open(self.path_data_raw, "w", encoding="utf-8") as outfile:
            json.dump(processed_documents, outfile, ensure_ascii=False)

    def transform_data(self) -> None:
        if not self.data_raw:
            self.data_raw = self._from_file(self.path_data_raw)

        documents = []
        for item in self.data_raw:
            title = item["title"]
            question = item["body"]
            answer = item["answer"]["body"]
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
                        "score": item["score"],
                    },
                )
            )

        self._to_file(self.path_data_processed, data=documents)
