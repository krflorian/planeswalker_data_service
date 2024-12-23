import logging
import time
from enum import Enum
from typing import List
from functools import cache

from chromadb import PersistentClient
from chromadb.utils import embedding_functions
from chromadb.api.models.Collection import Collection

from .document import ChromaDocument
from .config import ChromaConfig


class CollectionType(Enum):
    DOCUMENTS = "Documents"
    CARDS = "Cards"


class ChromaDB:

    def __init__(self, config: ChromaConfig):
        self.host = config.host
        self.port = config.port
        self.embedding_model = config.embedding_model
        self.embedding_device = config.embedding_device
        self.collection_2_name = {
            CollectionType.DOCUMENTS: config.collection_name_documents,
            CollectionType.CARDS: config.collection_name_cards,
        }
        self.collection_type_2_collection = {}
        self.client = PersistentClient(self.host)

    def __repr__(self):
        return f"ChromaDB(host:{self.host}, model:{self.embedding_model})"

    def get_collection(self, collection_type: CollectionType) -> Collection:
        """
        Retrieves or creates a ChromaDB collection.

        Returns:
            Collection: A ChromaDB collection object.
        Raises:
            Exception: If there's an error creating or retrieving the collection.
        """
        if not isinstance(collection_type, CollectionType):
            collection_type = CollectionType(collection_type)

        try:
            # Create embedding function
            collection = self.collection_type_2_collection.get(collection_type)
            if collection is not None:
                return collection

            ef = embedding_functions.SentenceTransformerEmbeddingFunction(
                self.embedding_model,
                device=self.embedding_device,
            )

            # Get or create collection
            collection_name = self.collection_2_name.get(collection_type)
            collection = self.client.get_or_create_collection(
                name=collection_name,
                embedding_function=ef,
                metadata={"hnsw:space": "cosine"},
            )
            self.collection_type_2_collection[collection_type] = collection

            logging.info(
                f"Successfully created collection {collection_name} with {collection.count()} documents"
            )

            return collection

        except Exception as e:
            logging.error(e, exc_info=True)
            raise

    def update_last_successful_load(self, collection) -> None:
        """
        Updates the last successful load timestamp within the collection metadata.

        Args:
            collection (Collection): The ChromaDB collection to be updated.

        Raises:
            Exception: If there's an error updating the collection.
        """

        try:
            collection.modify(metadata={"lastUpdate": round(time.time(), 2)})
            logging.info(
                f"Successfully updated the last successful load timestamp for {collection.name}."
            )
        except Exception as e:
            logging.exception(
                f"Error updating the last successful load timestamp for {collection.name}."
            )
            raise

    def upsert_documents_to_collection(
        self, documents: List[ChromaDocument], collection_type: CollectionType
    ) -> None:
        """
        Upserts documents into the ChromaDB collection.

        Args:
            documents (List[ChromaDocument]): List of documents to be upserted.
            collection (Collection): The target ChromaDB collection.

        Raises:
            Exception: If there's an error during the upsertion process.
        """
        collection = self.get_collection(collection_type=collection_type)

        try:
            ids = [document.id for document in documents]

            # Upsert documents
            collection.upsert(
                ids=ids,
                documents=[document.document for document in documents],
                metadatas=[document.metadata for document in documents],
            )

            logging.info(
                f"Successfully upserted {len(ids)} documents to the collection: {collection.name}."
            )

            # Update last successful load timestamp
            self.update_last_successful_load(collection)

        except Exception as e:
            logging.exception(
                f"Error upserting documents to the collection: {collection.name}."
            )
            raise

    def delete_documents_from_collection(
        self, collection_type: CollectionType, ids: List[str] = []
    ) -> None:
        """
        Deletes documents from the ChromaDB collection.

        Args:
            collection (Collection): The target ChromaDB collection.
            ids (List[str]): List of document IDs to be deleted.

        Raises:
            Exception: If there's an error during the deletion process.
        """
        collection = self.get_collection(collection_type)
        try:
            collection.delete(ids=ids)
            logging.info(
                f"Successfully deleted {len(ids)} documents from the collection: {collection.name}."
            )
        except Exception as e:
            logging.exception(
                f"Error deleting documents from the collection: {collection.name}."
            )
            raise

    def delete_collection(self, collection_type: CollectionType):

        collection_name = self.collection_2_name.get(collection_type)
        result = self.client.delete_collection(collection_name)
        return result
