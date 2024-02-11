# %%
import json
from pathlib import Path
from sentence_transformers import SentenceTransformer

from src.vector_db import VectorDB
from src.objects import Document

if __name__ == "__main__":
    # create variables
    db_name = "rules_db_gte"
    DATA_PATH = Path("./data")
    ETL_PATH = DATA_PATH / "processed/documents"
    ARTIFACT_PATH = DATA_PATH / "artifacts"

    # load documents
    documents = []
    for file in ETL_PATH.iterdir():
        if file.suffix != ".json":
            continue
        print(f"loading data from {file.name}")
        with file.open("r", encoding="utf-8") as infile:
            data = json.load(infile)
        documents.extend([Document(**d) for d in data])
    print(f"loaded {len(documents)} documents")

    # load model
    model = SentenceTransformer(
        "thenlper/gte-large"
    )  # sentence-transformers/all-MiniLM-L6-v2

    rules_db = VectorDB(
        texts=[doc.text for doc in documents],
        data=documents,
        model=model,
    )

    # save rules db
    rules_db.dump(ARTIFACT_PATH / f"{db_name}.p")
