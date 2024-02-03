from src.logging import get_logger
from transformers import Pipeline
from enum import Enum

logger = get_logger(__name__)


class Intent(Enum):
    DECKBUILDING = "deckbuilding"
    RULES = "rules"
    CONVERSATION = "conversation"
    # BAD_INTENTION = "bad_intention"


def classify_intent(text: str, classifier: Pipeline) -> tuple[str, float]:
    """Classify the user intent into one of the classes in Intent."""

    hypothesis_template = "You are a chatbot that answers magic the Gathering Questions. The user wants to talk about {}"

    intent_mapper = {
        "rules_question": "rules",
        "rules": "rules",
        "deck_building": "deckbuilding",
        "specific_cards": "deckbuilding",
        "card_info": "deckbuilding",
        "trading_cards": "deckbuilding",
        "illegal": "conversation",  # TODO should be its own class
        "cheating": "conversation",  # TODO should be its own class
        "greeting": "conversation",
    }

    output = classifier(
        text,
        list(intent_mapper.keys()),
        hypothesis_template=hypothesis_template,
        multi_label=False,
    )

    intent = intent_mapper[output["labels"][0]]
    score = output["scores"][0]

    logger.info(f"classified intent: {intent} {score:.2f}")
    return intent, score
