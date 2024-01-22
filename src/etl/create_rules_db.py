# %%
from pathlib import Path
from sentence_transformers import SentenceTransformer

from src.vector_db import VectorDB
from src.objects import Document


if __name__ == "__main__":
    # create variables
    db_name = "rules_db_gte"
    ETL_DATA_PATH = Path("data/etl")
    rules_db_file = Path(f"data/artifacts/{db_name}.p")

    # load model
    model = SentenceTransformer(
        "thenlper/gte-large"
    )  # sentence-transformers/all-MiniLM-L6-v2

    rules_db = VectorDB(
        texts=texts,
        data=rules,
        model=model,
    )

    # save rules db
    rules_db.dump(rules_db_file)
