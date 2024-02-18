import wikipedia
import random
import re
import json
from pathlib import Path
from datetime import datetime
from tqdm import tqdm

from src.objects import Document


def parse_keywords_from_wikipedia():
    # Specify the title of the Wikipedia page
    wiki = wikipedia.page("List of Magic: The Gathering keywords")
    now = datetime.now()

    # Extract the plain text content of the page, excluding images, tables, and other data.
    text = wiki.content
    keyword_pattern = r"(=== [^=]+ ===)"
    chapter_pattern = r"(== [^=]+ ==)"
    reference_pattern = r":\u200a(?:!\d+|\d+(?:,\u200a\d+)*)\u200a"
    processed_text = re.split(keyword_pattern, text)

    # add documents
    documents = []
    chapter = re.split(chapter_pattern, processed_text[0])[1]
    chapter = chapter.replace("==", "").strip()
    # print("chapter: ", chapter)
    for text in tqdm(processed_text[1:]):
        if text.startswith("==="):
            keyword = text.replace("===", "")
            keyword = keyword.strip()
        else:
            # delete chapter
            texts = re.split(chapter_pattern, text)
            if len(texts) > 1:
                chapter = texts[1]
                chapter = chapter.replace("==", "").strip()
                # print("chapter: ", chapter)
                text = texts[0]

            # clean text
            text = text.replace("\n", "")
            text = re.sub(reference_pattern, "", text)

            # create document
            doc = Document(
                name=f"Keyword: {keyword}",
                text=text,
                url=wiki.url,
                metadata={
                    "timestamp": str(now),
                    "chapter": chapter,
                    "origin": "wikipedia.com",
                },
                keywords=[keyword],
            )
            documents.append(doc)

    doc = random.choice(documents)
    print("___________________")
    print(f"Processed {len(documents)} Documents like this:")
    for key, value in doc.model_dump().items():
        print(key, ": ", value)
    print("___________________")
    return documents


if __name__ == "__main__":
    DATA_PATH = Path("../data")
    ETL_PATH = DATA_PATH / "etl"

    documents = parse_keywords_from_wikipedia()
    document_jsons = [doc.model_dump() for doc in documents]

    # save documents
    with open(
        ETL_PATH / "processed/documents/keywords.json", "w", encoding="utf-8"
    ) as outfile:
        json.dump(document_jsons, outfile, ensure_ascii=False)

    # save keywords as list
    keywords = []
    for doc in documents:
        keywords.extend(doc.keywords)
    keywords = list(set(keywords))
    with open(ETL_PATH / "raw/keyword_list.json", "w", encoding="utf-8") as outfile:
        json.dump(keywords, outfile, ensure_ascii=False)
