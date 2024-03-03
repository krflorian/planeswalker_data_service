# %%
import json
from pydantic import BaseModel
from tqdm import tqdm
from stackapi import StackAPI
from datetime import datetime
from pathlib import Path


class StackExchangeExtractor(BaseModel):
    raw_filepath = Path("../data/etl/raw/documents/stackoverflow.json")

    site = StackAPI("boardgames")
    tags = ["mtg-stack", "mtg-commander", "magic-the-gathering"]
    site.page_size = 50
    site.max_pages = 1

    processed_documents = []
    for year in tqdm(range(2010, 2025)):
        for tag in tags:
            questions = site.fetch(
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
                answers = site.fetch(
                    "answers",
                    ids=[item["accepted_answer_id"] for item in questions_with_answers],
                    tagged="magic-the-gathering",
                    filter="withbody",
                )
                anwer_id_2_answer = {
                    answer["answer_id"]: answer for answer in answers["items"]
                }

                for item in questions_with_answers:
                    item["answer"] = anwer_id_2_answer[item["accepted_answer_id"]]
                    processed_documents.append(item)

    len(processed_documents)

    with open(
        "../data/etl/raw/documents/stackoverflow.json", "w", encoding="utf-8"
    ) as outfile:
        json.dump(processed_documents, outfile, ensure_ascii=False)


# %%


# data processor

# extract_data
# speichert als raw ab
# transform_data
# speichert als document json ab
