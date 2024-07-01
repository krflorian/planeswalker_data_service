import logging
from datetime import datetime
from .chroma_collection import ChromaCollection
from .extractor import Extractor
from .request import get_request
from chromadb.api.models.Collection import Collection
from typing import Optional, List
from pydantic import Field

class GlossaryExtractor(Extractor):
    collection_name: str = Field('crRules', description="Collection name from ChromaDB")
    glossary: Optional[List] = Field(None, description="Collection object from ChromaDB")


    def get_data(self):
        updates = get_request(api_url="https://api.academyruins.com/diff/cr")

        if len(self.loader.collection.get(where={"documentType" : "glossary"})['ids']) == 0 or self.config["ETL_MODE"] == 'full':
            self.full_extract()
        elif self.loader.collection.metadata['lastUpdate'] < datetime.strptime(updates['creationDay'], "%Y-%m-%d").timestamp():
            self.full_extract()
        else: 
            print(f"collection {self.loader.collection_name} is up-to-date with latest data from {updates['creationDay']}")
            return

        self.transform_data()
        self.loader.upsert_documents_to_collection(self.documents)
        return

    def full_extract(self) -> list[ChromaCollection]: 
        logging.info(f"Starting full-extraction")
        # extract glossary
        off_glossary = get_request("https://api.academyruins.com/cr/glossary") 
        logging.info(f"Successfully extracted {len(off_glossary)} glossary entries")

        unoff_glossary = get_request("https://api.academyruins.com/cr/unofficial-glossary") 
        logging.info(f"Successfully extracted {len(unoff_glossary)} unofficial-glossary entries")

        self.glossary = {**off_glossary, **unoff_glossary}

    def transform_data(self) -> list[ChromaCollection]:
        logging.info(f"Starting transformation")
        # transform rules
        documents = []

        for entry in self.glossary.values():
            document = ChromaCollection(
                id = entry['term'],
                document = f"{entry['term']}: {entry['definition']}",
                metadata = {
                    "documentType": "glossary",
                    "combined_title": f"Glossary Entry for {entry['term']}",
                    "url": f"https://yawgatog.com/resources/magic-rules/#R{entry['term'][0].lower()}"
                }
            )
            documents.append(document)
        self.documents = documents
        logging.info(f"Successfully transformed data")