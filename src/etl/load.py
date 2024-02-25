from pydantic import BaseModel, Field
import json
from pathlib import Path
from sentence_transformers import SentenceTransformer

from src.objects import Document
from src.vector_db import VectorDB

class DataLoader(BaseModel):
    path_database: Path
    path_data_processed: Path = Path("../data/etl/processed/documents/")
    data_processed: list = Field(default_factory=list)

    def load_data(self):
            # load documents

            for file in self.path_data_processed.iterdir():
                if file.suffix != ".json":
                    continue
                print(f"loading data from {file.name}")
                with file.open("r", encoding="utf-8") as infile:
                    data = json.load(infile)
                self.data_processed.extend([Document(**d) for d in data])
            print(f"loaded {len(self.data_processed)} documents")

            # load model
            model = SentenceTransformer(
                "thenlper/gte-large"
            )  # sentence-transformers/all-MiniLM-L6-v2

            rules_db = VectorDB(
                texts=[doc.text for doc in self.data_processed],
                data=self.data_processed,
                model=model,
            )

            # save rules db
            rules_db.dump(self.path_database)

class RulesDB(DataLoader):
    path_database: Path = Path("../data/artifacts/rules_db_gte.p")
    path_data_processed: Path = Path("../data/etl/processed/documents/")