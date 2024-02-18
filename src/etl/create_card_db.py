# %%
import json
from pathlib import Path
from sentence_transformers import SentenceTransformer

from src.vector_db import VectorDB
from src.objects import Card, Document


def parse_card_data(data: list[dict], keywords: list[str]) -> list[Card]:
    cards = []
    for card_data in data:
        rules = card_data.get("rulings", [])
        rules = [
            Document(
                name=f"Ruling #{idx} for {card_data.get('name')}",
                text=text,
                url=card_data.get("related_uris", {}).get(
                    "gatherer", card_data.get("rulings_uri")
                ),
                metadata={"origin": f"Special Ruling for {card_data.get('name')}"},
                keywords=[
                    keyword for keyword in keywords if keyword.lower() in text.lower()
                ],
            )
            for idx, text in enumerate(rules)
        ]
        cards.append(
            Card(
                _id=card_data.get("id"),
                name=card_data.get("name"),
                mana_cost=card_data.get("mana_cost"),
                type=card_data.get("type_line"),
                power=card_data.get("power", "0"),
                toughness=card_data.get("toughness", "0"),
                oracle=card_data.get("oracle_text", ""),
                price=card_data.get("prices", {}).get("eur", 0.0) or 0.0,
                color_identity=card_data.get("color_identity", []),
                keywords=card_data.get("keywords", []),
                legalities=card_data.get("legalities", {}),
                url=card_data.get("related_uris", {}).get(
                    "gatherer", card_data.get("image_uris", {}).get("large")
                ),
                rulings=rules,
            )
        )

    print(f"parsed {len(cards)} cards")
    return cards


def create_card_db(cards: list[Card], model: SentenceTransformer) -> VectorDB:
    texts, cards_in_db = [], []
    for card in cards:
        texts.append(card.to_text(include_price=False))
        cards_in_db.append(card)

        texts.append(card.name)
        cards_in_db.append(card)

    card_db = VectorDB(
        texts=texts,
        data=cards_in_db,
        model=model,
    )
    return card_db


if __name__ == "__main__":
    # create variables
    db_name = "card_db_gte"
    UPDATE_DATABASE = False
    DATA_PATH = Path("../data")
    ARTIFACT_PATH = DATA_PATH / "artifacts"
    ALL_CARDS_FILE = DATA_PATH / "etl/raw/cards/scryfall_all_cards_with_rulings.json"
    KEYWORD_FILE = DATA_PATH / "etl/raw/keyword_list.json"

    # load model
    model = SentenceTransformer("../data/models/gte-large")

    # load data
    with ALL_CARDS_FILE.open("r", encoding="utf-8") as infile:
        data = json.load(infile)
    with KEYWORD_FILE.open("r", encoding="utf-8") as infile:
        keywords = json.load(infile)

    cards = parse_card_data(data=data, keywords=keywords)

    # if update:
    if UPDATE_DATABASE:
        card_db = VectorDB.load(ARTIFACT_PATH / f"{db_name}.p")
        card_names_vectorized = [c.name for c in card_db.ids_2_data.values()]
        cards_new = [c for c in cards if c.name not in card_names_vectorized]
        embeddings_and_data = card_db.get_embeddings(
            [card.to_text(include_price=False) for card in cards_new], cards_new, model
        )
        card_db.add(embeddings_and_data)
    else:
        card_db = create_card_db(cards, model)

    # save
    card_db.dump(ARTIFACT_PATH / f"{db_name}.p")
