# %%
import requests
import json
from tqdm import tqdm
from pathlib import Path
from sentence_transformers import SentenceTransformer

from logging_utils import get_logger
from vector_db import VectorDB
from objects import Card, Document

BLOCKED_CARD_TYPES = ["Card", "Stickers", "Hero"]
NORMAL_CARD_TYPES = [
    "saga",
    "case",
    "adventure",
    "prototype",
    "augment",
    "mutate",
    "leveler",
    "class",
    "host",
    "normal",
]
DOUBLE_FACED = ["transform", "card_faces", "flip", "split"]

logger = get_logger()


def download_card_data(
    lookup_url: str = "https://api.scryfall.com/bulk-data",
) -> list[dict]:

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
        and ((card["layout"] in NORMAL_CARD_TYPES) or (card["layout"] in DOUBLE_FACED))
    ]

    logger.info(f"saving {len(data)} raw card data")
    return data


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

        url = card_data.get("related_uris", {}).get(
            "gatherer", card_data.get("image_uris", {}).get("large")
        )
        if url is None:
            url = card_data["related_uris"].get("edhrec")

        if card_data.get("layout") in NORMAL_CARD_TYPES:
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
                    url=url,
                    rulings=rules,
                )
            )
        elif card_data.get("layout") in DOUBLE_FACED:
            for card_face in card_data.get("card_faces"):
                cards.append(
                    Card(
                        _id=card_data.get("id"),
                        name=card_face.get("name"),
                        mana_cost=card_face.get("mana_cost"),
                        type=card_face.get("type_line"),
                        power=card_data.get("power", "0"),
                        toughness=card_data.get("toughness", "0"),
                        oracle=card_face.get("oracle_text", ""),
                        price=card_data.get("prices", {}).get("eur", 0.0) or 0.0,
                        color_identity=card_data.get("color_identity", []),
                        keywords=card_data.get("keywords", []),
                        legalities=card_data.get("legalities", {}),
                        url=url,
                        rulings=rules,
                    )
                )

    logger.info(f"parsed {len(cards)} cards")
    return cards


def create_card_db(cards: list[Card], model: SentenceTransformer) -> VectorDB:
    texts, cards_in_db = [], []
    for card in cards:
        texts.append(card.to_text(include_price=False))
        cards_in_db.append(card)

        texts.append(card.name)
        cards_in_db.append(card)

    logger.info(f"creating vector db with {len(cards)} cards")
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
    KEYWORD_FILE = DATA_PATH / "etl/raw/documents/keyword_list.json"

    # load card data
    data = download_card_data()
    # save data
    with ALL_CARDS_FILE.open("w", encoding="utf-8") as outfile:
        json.dump(data, outfile, ensure_ascii=False)

    # load model
    model = SentenceTransformer("../data/models/gte-large")
    logger.info(f"loaded sentence transformer on device: {model.device}")

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
    logger.info(f"created card db with {len(cards)} cards")
