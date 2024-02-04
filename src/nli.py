from src.logging import get_logger
from transformers import Pipeline
from enum import Enum

logger = get_logger(__name__)


class Intent(Enum):
    DECKBUILDING = "deckbuilding"
    RULES = "rules"
    CONVERSATION = "conversation"
    MALICIOUS = "malicious"


INTENT_MAPPER = {
    "rules_question": Intent.RULES,
    "rules": Intent.RULES,
    "deck_building": Intent.DECKBUILDING,
    "specific_cards": Intent.DECKBUILDING,
    "card_info": Intent.DECKBUILDING,
    "trading_cards": Intent.DECKBUILDING,
    "greeting": Intent.CONVERSATION,
    "illegal": Intent.MALICIOUS,
    "cheating": Intent.MALICIOUS,
    "code": Intent.MALICIOUS,
    "program": Intent.MALICIOUS,
    "script": Intent.MALICIOUS,
}


def classify_intent(text: str, classifier: Pipeline) -> tuple[str, float]:
    """Classify the user intent into one of the classes in Intent."""

    hypothesis_template = "You are a chatbot that answers magic the Gathering Questions. The user wants to talk about {}"

    output = classifier(
        text,
        list(INTENT_MAPPER.keys()),
        hypothesis_template=hypothesis_template,
        multi_label=False,
    )

    intent = INTENT_MAPPER.get(output["labels"][0], "greeting")
    score = output["scores"][0]

    logger.info(f"classified intent: {intent} {score:.2f}")
    return intent, score
