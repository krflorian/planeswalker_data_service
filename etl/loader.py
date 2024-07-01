from .chroma_collection import ChromaCollection
from chromadb import HttpClient
from chromadb.utils import embedding_functions
from chromadb.api.models.Collection import Collection
from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict

import time
import logging


class Loader(BaseModel):
    config: Dict = Field(None, description="Config for ChromaDB")
    collection_name: str = Field('crRulesss', description="Name of the collection in ChromaDB")
    collection: Optional[Collection] = Field(None, description="Collection object from ChromaDB")

    def model_post_init(self, __context: Any) -> None:
        self.collection = self.get_collection()

    def get_collection(self) -> Collection:
        """
        Retrieves or creates a ChromaDB collection.

        Returns:
            Collection: A ChromaDB collection object.
        Raises:
            Exception: If there's an error creating or retrieving the collection.
        """

        try:
            # Create ChromaDB client
            client = HttpClient(self.config["CHROMA_HOST"], int(self.config["CHROMA_PORT"]))

            # Create embedding function
            ef = embedding_functions.SentenceTransformerEmbeddingFunction(
                self.config["EMBEDDING_FUNCTION"], device=self.config["EMBEDDING_DEVICE"])

            # Get or create collection
            collection = client.get_or_create_collection(
                name=self.collection_name, embedding_function=ef)

            logging.info(f"Successfully created collection {self.collection_name} with {collection.count()} documents")

            return collection
        except Exception as e:
            logging.exception("Error creating or retrieving the collection.")
            raise

    def update_last_successful_load(self) -> None:
        """
        Updates the last successful load timestamp within the collection metadata.

        Args:
            collection (Collection): The ChromaDB collection to be updated.
        
        Raises:
            Exception: If there's an error updating the collection.
        """

        try:
            self.collection.modify(metadata={
                "lastUpdate": round(time.time(), 2)
            }) 
            logging.info(f"Successfully updated the last successful load timestamp for {self.collection.name}.")
        except Exception as e:
            logging.exception(f"Error updating the last successful load timestamp for {self.collection.name}.")
            raise

    def upsert_documents_to_collection(self, documents: List[ChromaCollection]) -> None:
        """
        Upserts documents into the ChromaDB collection.

        Args:
            documents (List[ChromaDocument]): List of documents to be upserted.
            collection (Collection): The target ChromaDB collection.

        Raises:
            Exception: If there's an error during the upsertion process.
        """

        try:
            ids = [document.id for document in documents]

            # Upsert documents
            self.collection.upsert(
                ids=ids, 
                documents=[document.document for document in documents],
                metadatas=[document.metadata for document in documents]
            )

            logging.info(f"Successfully upserted {len(ids)} documents to the collection: {self.collection.name}.")

            # Update last successful load timestamp
            self.update_last_successful_load()

        except Exception as e:
            logging.exception(f"Error upserting documents to the collection: {self.collection.name}.")
            raise

    def delete_documents_from_collection(self, ids: List[str] = []) -> None:
        """
        Deletes documents from the ChromaDB collection.

        Args:
            collection (Collection): The target ChromaDB collection.
            ids (List[str]): List of document IDs to be deleted.

        Raises:
            Exception: If there's an error during the deletion process.
        """

        try:
            self.collection.delete(ids=ids)
            logging.info(f"Successfully deleted {len(ids)} documents from the collection: {self.collection.name}.")
        except Exception as e:
            logging.exception(f"Error deleting documents from the collection: {self.collection.name}.")
            raise



