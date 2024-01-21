from src.logging import get_logger
from transformers import Pipeline
from enum import Enum

logger = get_logger(__name__)


class Intent(Enum):
    DECKBUILDING = "deckbuilding"
    RULES = "rules"
    CONVERSATION = "conversation"


def classify_intent(text: str, classifier: Pipeline) -> tuple[float, Intent]:
    """Classify the user intent into one of the classes in Intent."""
    output = classifier(text, [intent.value for intent in Intent])
    intent = output["labels"][0]
    score = output["scores"][0]
    logger.info(f"classified intent: {intent} {score:.2f}")

    return intent, score
