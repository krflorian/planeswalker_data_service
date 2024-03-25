import re
from typing import Any
import hnswlib
import pickle
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer

from logging_utils import get_logger

logger = get_logger(__name__)


class VectorDB:
    def __init__(self, texts: list[str], data: list[Any], model: SentenceTransformer):
        """Initialize HNSW Graph.

        Infos and Documentation: https://github.com/nmslib/hnswlib
        """
        self.graph: hnswlib.Index = None
        self.ids_2_data: dict[int, str] = None

        embeddings_and_data = self.get_embeddings(texts, data, model)
        self.create_graph(embeddings_and_data=embeddings_and_data)

    def get_embeddings(
        self, texts: list[str], data: list[Any], model: SentenceTransformer
    ) -> tuple[str, np.ndarray]:
        """texts and data must be coindexed"""
        assert len(texts) == len(data), "texts and data must be coindexed"

        logger.info(f"creating {len(texts)} embeddings")
        embeddings = self.vectorize_texts(texts, model)

        embeddings_and_data = []
        for embedding, d in zip(embeddings, data):
            embeddings_and_data.append((np.array(embedding), d))

        return embeddings_and_data

    def create_graph(
        self,
        embeddings_and_data: list[tuple[np.ndarray, Any]],
        ef: int = 10000,
        M: int = 16,
    ) -> None:
        """Create the Search Graph.

        Parameters:
            embeddings_and_data: a list of tuples (vector, some_data_object)
            ef: parameter that controls speed/accuracy trade-off during the index construction
            M: parameter that defines the maximum number of outgoing connections in the graph
        """
        # Generating sample data
        if not embeddings_and_data:
            return
        embeddings, data = zip(*embeddings_and_data)
        embeddings = np.array(embeddings)
        ids = np.arange(len(data))

        # Declaring index
        graph = hnswlib.Index(space="cosine", dim=len(embeddings[0]))
        graph.init_index(max_elements=len(embeddings), ef_construction=ef, M=M)
        graph.add_items(embeddings, ids)
        graph.set_ef(ef)

        self.graph = graph
        self.ids_2_data = {idx: d for idx, d in zip(ids, data)}

        return

    def add(self, embeddings_and_data) -> None:
        """Add labels and embeddings to the Search Graph."""
        if not embeddings_and_data:
            return
        embeddings, data = zip(*embeddings_and_data)
        logger.info(f"adding {len(data)} embeddings")

        old_index_size = self.graph.get_max_elements()
        new_index_size = old_index_size + len(embeddings_and_data)
        idxs = [old_index_size + i for i in range(len(embeddings))]

        self.graph.resize_index(new_index_size)
        self.graph.add_items(data=embeddings, ids=idxs)
        self.ids_2_data.update({idx: d for idx, d in zip(idxs, data)})

    def query(
        self,
        text: str,
        model: SentenceTransformer,
        k: int = 5,
        threshold: float = 0.2,
        lasso_threshold: int = 0.02,
        split_pattern: str = "\.|\?",
    ) -> list[str, float]:
        """Search for similar entries in Vector DB.

        Parameters:
            text: query text
            k: how many results should be returned
            threshhold: what is the max distance for the search query
            lasso_threshold: distance between most similar and everything else
            split_pattern: how the query text is processed

        Returns: a list of entries in the vector db and their distance to the search query text.
        """
        search_results = []
        sentences = [s for s in re.split(split_pattern, text) if s != ""]
        embeddings = self.vectorize_texts(sentences, model)
        for embedding in embeddings:
            idxs, distances = self.graph.knn_query(embedding, k=min(k, 5))

            baseline_distance = distances[0][0]
            for idx, distance in zip(idxs[0], distances[0]):
                if (distance - baseline_distance < lasso_threshold) and (
                    distance < threshold
                ):
                    search_results.append((self.ids_2_data.get(idx, None), distance))

        search_results = sorted(search_results, key=lambda x: x[1])[:k]
        logger.info(f"retrieved {len(search_results)} documents")

        return search_results

    def vectorize_texts(
        self, texts: list[str], model: SentenceTransformer
    ) -> np.ndarray:
        """Create a np.array from text."""
        embeddings = model.encode(texts, show_progress_bar=True)
        return embeddings

    def sample_results(self, search_results: tuple[Any, float], k: 5) -> list[str]:
        """Create a random sample of the results weighted with their distance to the search query."""

        if not search_results:
            return []

        k = min(k, len(search_results))
        weights = [result[1] for result in search_results]
        normalized_weights = normalize_weights(weights)

        idxs = list(
            np.random.choice(
                range(len(search_results)),
                size=k,
                replace=False,
                p=normalized_weights,
            )
        )

        return [result for idx, result in enumerate(search_results) if idx in idxs]

    @classmethod
    def load(self, filepath: Path):
        if not isinstance(filepath, Path):
            filepath = Path(filepath)
        if not filepath.is_file():
            logger.error(f"There is no file '{filepath}'")
            raise ValueError(filepath)

        with filepath.open("rb") as infile:
            vector_db: VectorDB = pickle.load(infile)
        logger.info(f"loaded vector db with {len(vector_db.ids_2_data)} documents")
        return vector_db

    def dump(self, filepath: Path):
        with filepath.open("wb") as outfile:
            pickle.dump(self, outfile)
        logger.info(
            f"dumped vector db with {len(self.ids_2_data)} documents in {filepath}"
        )
        return


def normalize_weights(weights):
    normalized_weights = np.array(weights) / np.sum(weights)

    # Check if the sum is exactly 1
    if not np.isclose(np.sum(normalized_weights), 1.0):
        # Adjust the last element to make the sum exactly 1
        normalized_weights[-1] += 1.0 - np.sum(normalized_weights)

    return normalized_weights
