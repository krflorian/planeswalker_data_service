# %%
from src.vector_db import VectorDB
from src.objects import Card, Rule

from tqdm import tqdm
from pathlib import Path
from sentence_transformers import SentenceTransformer
import requests
import json


def download_card_data(
    lookup_url: str = "https://api.scryfall.com/bulk-data",
) -> list[dict]:
    BLOCKED_CARD_TYPES = ["Card", "Stickers", "Hero"]

    # download info
    bulk_requests_info = requests.get(lookup_url)
    bulk_requests_info = bulk_requests_info.json()

    # download cards data
    oracl_card_info = [
        info for info in bulk_requests_info["data"] if info["type"] == "oracle_cards"
    ][0]
    oracle_cards_url = oracl_card_info["download_uri"]
    oracle_card_data = requests.get(oracle_cards_url)
    oracle_card_data = oracle_card_data.json()

    # download rulings
    rulings_info = [
        info for info in bulk_requests_info["data"] if info["type"] == "rulings"
    ][0]
    rulings_info_url = rulings_info["download_uri"]
    rulings_data = requests.get(rulings_info_url)
    rulings_data = rulings_data.json()

    # combine
    idx_2_card_data = {
        card_data["oracle_id"]: card_data for card_data in oracle_card_data
    }

    for ruling in tqdm(rulings_data):
        oracle_id = ruling["oracle_id"]
        if "rulings" not in idx_2_card_data[oracle_id]:
            idx_2_card_data[oracle_id]["rulings"] = []
        idx_2_card_data[oracle_id]["rulings"].append(ruling["comment"])

    # clean card data
    data = [
        card
        for card in idx_2_card_data.values()
        if (card["type_line"] not in BLOCKED_CARD_TYPES)
        and (card["layout"] == "normal")
    ]

    return data


def save_card_data(data: list[dict], all_cards_file: Path) -> None:
    # save all cards
    print(f"saving cards data with {len(data)} cards")

    with all_cards_file.open("w", encoding="utf-8") as outfile:
        json.dump(data, outfile)


def parse_card_data(data: list[dict]) -> list[Card]:
    cards = []
    for card_data in data:
        rules = card_data.get("rulings", [])
        rules = [
            Rule(
                text=text,
                rule_id=str(idx),
                chapter="Card Ruling",
                subchapter=card_data.get("name"),
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
                image_url=card_data["image_uris"].get("large"),
                rulings=rules,
            )
        )

    return cards


def create_card_db(cards: list[Card]) -> VectorDB:
    texts, cards = [], []
    for card in cards:
        texts.append(card.to_text(include_price=False))
        cards.append(card)

    card_db = VectorDB(
        texts=texts,
        data=cards,
        model=model,
    )
    return card_db


# %%

if __name__ == "__main__":
    # create variables
    db_name = "card_db_gte"
    cards_data_path = Path("../data/cards")
    artifacts_path = Path("../data/artifacts")
    all_cards_file = cards_data_path / "scryfall_all_cards_with_rulings.json"

    # load model
    model = SentenceTransformer("../data/models/gte-large")

    # load data
    data = download_card_data()
    save_card_data(data=data, all_cards_file=all_cards_file)
    cards = parse_card_data(data=data)

    # if update:
    try:
        card_db = VectorDB.load(artifacts_path / f"{db_name}.p")
        card_names_vectorized = [c.name for c in card_db.ids_2_data.values()]
        cards_new = [c for c in cards if c.name not in card_names_vectorized]
        texts, cards = [], []
        for card in cards_new:
            texts.append(card.to_text(include_price=False))
            cards.append(card)
        embeddings_and_data = card_db.get_embeddings(texts, cards, model)
        card_db.add(embeddings_and_data)
    except:
        cards_new = cards[:]
        texts, cards = [], []
        for card in cards_new:
            texts.append(card.to_text(include_price=False))
            cards.append(card)
        card_db = VectorDB(texts, cards, model=model)

    # save
    card_db.dump(artifacts_path / f"{db_name}.p")
