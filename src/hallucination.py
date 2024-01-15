# %%

from sentence_transformers import CrossEncoder
from src.logging import get_logger

logger = get_logger(__name__)


def validate_answer(
    answer: str, rag_chunks: list[str], model: CrossEncoder
) -> list[float]:
    data = []
    for chunk in rag_chunks:
        data.append([answer, chunk])
    logger.info(f"checking {len(rag_chunks)} chunks for halucination")
    scores = model.predict(data, show_progress_bar=True)
    return scores
