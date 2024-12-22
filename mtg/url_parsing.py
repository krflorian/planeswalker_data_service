import re
import logging

from mtg.objects import Card


def parse_card_names(text: str, card_name_2_card: dict[str, Card]) -> str:
    pattern = r"<<([^<>]+)>>"
    matches = re.findall(pattern, text)

    for match in list(set(matches)):
        card = card_name_2_card.get(match, None)
        if card is not None:
            logging.info(f"parsing card name: {card.name}")
            text = text.replace(f"<<{match}>>", f"[{card.name}]({card.url})")
        else:
            text = text.replace(f"<<{match}>>", match)
    return text
