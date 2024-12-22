import re
import wikipedia
from pathlib import Path
from datetime import datetime
import logging

from mtg.objects import Document
from mtg.logging import get_logger
from .data_extractor import DataExtractor

logger = get_logger()

PROCESSED_DATA_PATH = Path("../data/etl/processed/documents/")
RAW_DATA_PATH = Path("../data/etl/raw/documents/")


class WikipediaExtractor(DataExtractor):
    api_url: str = "List of Magic: The Gathering keywords"
    path_data_raw: Path = RAW_DATA_PATH / "wikipedia.txt"
    path_data_processed: Path = PROCESSED_DATA_PATH / "wikipedia.json"

    def extract_data(self) -> None:
        # Specify the title of the Wikipedia page
        wiki = wikipedia.page(self.api_url)
        text = wiki.content

        self.data_raw = text
        with open(self.path_data_raw, "w", encoding="utf-8") as outfile:
            outfile.write(text)

        logger.info(
            f"downloaded page {self.api_url} from wikipedia saving in {self.path_data_raw}"
        )

    def transform_data(self) -> None:
        if not self.data_raw:
            self.data_raw = self._from_file(self.path_data_raw)

        url = wikipedia.page(self.api_url).url
        now = datetime.now()

        keyword_pattern = r"(=== [^=]+ ===)"
        chapter_pattern = r"(== [^=]+ ==)"
        reference_pattern = r":\u200a(?:!\d+|\d+(?:,\u200a\d+)*)\u200a"
        processed_text = re.split(keyword_pattern, self.data_raw)

        # add documents
        documents = []
        chapter = re.split(chapter_pattern, processed_text[0])[1]
        chapter = chapter.replace("==", "").strip()

        logger.info(f"Transforming {len(processed_text)} items from Stackexchange")
        for text in processed_text[1:]:
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
                    url=url,
                    metadata={
                        "timestamp": str(now),
                        "chapter": chapter,
                        "origin": "wikipedia.com",
                    },
                    keywords=[keyword],
                )
                documents.append(doc)

        logger.info(
            f"saving {len(documents)} processed Wikipedia documents in {self.path_data_processed}"
        )
        self._to_file(self.path_data_processed, data=documents)

        return
