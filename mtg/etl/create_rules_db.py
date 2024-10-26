# %%
from pathlib import Path

from mtg.logging import get_logger
from mtg.etl.extractors import (
    RulesGuruExtractor,
    ComprehensiveRulesExtractor,
    StackExchangeExtractor,
    WikipediaExtractor,
)

logger = get_logger()

# %%
# setup extractors
DATA_RAW = Path("../data/etl/raw/documents")
DATA_PROCESSED = Path("../data/etl/processed/documents")

rules_guru = RulesGuruExtractor(
    path_data_raw=DATA_RAW / "rulesguru.json",
    path_data_processed=DATA_PROCESSED / "rulesguru.json",
)
comprehensive_rules = ComprehensiveRulesExtractor(
    path_data_raw=DATA_RAW / "comprehensive_rules.txt",
    path_data_processed=DATA_PROCESSED / "comprehensive_rules.json",
)

stack_exchange = StackExchangeExtractor(
    path_data_raw=DATA_RAW / "stackexchange.json",
    path_data_processed=DATA_PROCESSED / "stackexchange.json",
)

wikipedia = WikipediaExtractor(
    path_data_raw=DATA_RAW / "wikipedia.txt",
    path_data_processed=DATA_PROCESSED / "wikipedia.json",
)


extractors = [rules_guru, comprehensive_rules, stack_exchange, wikipedia]

# extractors = [rules_guru]

# %%
# fire extractors

for extractor in extractors:
    extractor.get_data_raw()
    extractor.get_data_processed()


# %%
# setup rules db
import json
from mtg.objects import Document
from mtg.chroma.config import ChromaConfig
from mtg.chroma.chroma_db import ChromaDB, CollectionType
from mtg.chroma import ChromaDocument

from tqdm import tqdm
from mtg.util import load_config
from uuid import uuid4

documents = []
for file in DATA_PROCESSED.iterdir():
    with file.open("r", encoding="utf-8") as infile:
        data = json.load(infile)
        for doc in data:
            documents.append(Document(**doc))

len(documents)

# %%


def batch(iterable, batch_size=1):
    length = len(iterable)
    for idx in range(0, length, batch_size):
        yield iterable[idx : min(idx + batch_size, length)]


logger.info("starting load")
config = load_config("configs/config.yaml")

chroma_config = ChromaConfig(**config["CHROMA"])
db = ChromaDB(chroma_config)

batch_size = 100
batches = batch(documents, batch_size)
for mini_batch in tqdm(
    batches, desc="uploading documents", total=len(documents) // batch_size
):

    documents = []
    for doc in mini_batch:
        metadata = {
            key: value for key, value in doc.to_chroma().items() if value is not None
        }
        documents.append(
            ChromaDocument(
                id=str(uuid4()),
                document=doc.text,
                metadata=metadata,
            )
        )

    db.upsert_documents_to_collection(
        documents=documents, collection_type=CollectionType.DOCUMENTS
    )


# %%

while True:
    mini_batch = next(batches)
    documents = []
    for doc in mini_batch:
        metadata = {
            key: value for key, value in doc.to_chroma().items() if value is not None
        }
        documents.append(
            ChromaDocument(
                id=str(uuid4()),
                document=doc.text,
                metadata=metadata,
            )
        )

    db.upsert_documents_to_collection(
        documents=documents, collection_type=CollectionType.DOCUMENTS
    )
