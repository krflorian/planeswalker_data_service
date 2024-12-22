# %%
import os
import requests
import json
from uuid import uuid4
from tqdm import tqdm
from pathlib import Path
from datetime import datetime

from mtg.util import load_config
from mtg.logging import get_logger
from mtg.objects import Card, Document

# from mtg.etl.cards.categorizer import create_categorizer
from mtg.chroma import ChromaDocument

from mtg.util import load_config
from mtg.chroma.config import ChromaConfig
from mtg.chroma.chroma_db import ChromaDB, CollectionType


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


def batch(iterable, batch_size=1):
    """Yield successive n-sized chunks from iterable."""
    length = len(iterable)
    for idx in range(0, length, batch_size):
        yield iterable[idx : min(idx + batch_size, length)]


def download_card_data(
    lookup_url: str = "https://api.scryfall.com/bulk-data",
) -> list[dict]:
    """Downloads card data from the Scryfall API and returns a list of card data."""

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

    for ruling in tqdm(rulings_data, desc="adding rulings to cards"):
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
    """Parses card data and returns a list of Card objects."""

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
                    id=card_data.get("id"),
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
            for face_num, card_face in enumerate(card_data.get("card_faces")):
                cards.append(
                    Card(
                        id=card_data.get("id") + f"_{face_num}",
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


def update_cards(
    all_cards_file: Path,
    all_keywords_file: Path,
    processed_cards_folder: Path,
    db: ChromaDB,
) -> bool:
    """Updates the card database by performing the following steps:
    1. Extract: Downloads card data and saves it to a file.
    2. Transform: Processes the card data, categorizes new cards, and saves them to a folder.
    3. Load: Adds new cards to the ChromaDB collection.
    Args:
        all_cards_file (Path): Path to the file where all card data will be saved.
        all_keywords_file (Path): Path to the file containing keywords for processing cards.
        processed_cards_folder (Path): Path to the folder where processed card data will be saved.
        db (ChromaDB): Instance of the ChromaDB database.
    Returns:
        bool: True if new cards were added to the database, False otherwise.
    """

    ##################################
    # 1. Extract: download card data #
    ##################################

    logger.info("starting extract")
    data = download_card_data()
    # save data
    with all_cards_file.open("w", encoding="utf-8") as outfile:
        json.dump(data, outfile, ensure_ascii=False)

    ###################################
    # 2. Transform: process card data #
    ###################################
    logger.info("starting transform")
    with all_keywords_file.open("r", encoding="utf-8") as infile:
        keywords = json.load(infile)

    processed_card_ids = set([file.stem for file in processed_cards_folder.iterdir()])

    cards = parse_card_data(data=data, keywords=keywords)
    new_cards = [card for card in cards if card.id not in processed_card_ids]
    # chat = create_categorizer("gpt-4o")
    for card in tqdm(new_cards, desc="Transforming cards"):
        """
        response = chat.invoke({"card_text": card.to_text()})

        categories = json.loads(
            response.additional_kwargs["function_call"]["arguments"]
        )
        categories = [k for k, v in categories.items() if v]
        card.categories = categories
        """

        card_data = card.to_dict()
        with open(
            processed_cards_folder / f"{card.id}.json", "w", encoding="utf-8"
        ) as outfile:
            json.dump(card_data, outfile, ensure_ascii=False)

    ######################################
    # 3. Load: add to Chroma Collection ##
    ######################################
    logger.info("starting load")

    # search cards in db
    collection = db.get_collection(CollectionType.CARDS)
    documents = collection.get()
    cards_in_db = set([doc["name"] for doc in documents["metadatas"]])
    new_cards = [card for card in cards if card.name not in cards_in_db]

    batch_size = 100
    batches = batch(new_cards, batch_size)
    for mini_batch in tqdm(
        batches, desc="uploading documents", total=len(new_cards) // batch_size
    ):

        documents = []
        for card in mini_batch:

            text = f"""
            {card.name}
            {card.type}
            {card.oracle}
            """
            documents.append(
                ChromaDocument(
                    id=str(uuid4()),
                    document=text,
                    metadata=card.to_chroma(),
                )
            )

        db.upsert_documents_to_collection(
            documents=documents, collection_type=CollectionType.CARDS
        )

    collection.modify(metadata={"last_updated": str(datetime.now())})
    return len(new_cards)


if __name__ == "__main__":
    # create variables

    config = load_config("../configs/config.yaml")
    os.environ["OPENAI_API_KEY"] = config.get("open_ai_token")

    DATA_PATH = Path("../data")
    ALL_CARDS_FILE = DATA_PATH / "etl/raw/cards/scryfall_all_cards_with_rulings.json"
    KEYWORD_FILE = DATA_PATH / "etl/raw/documents/keyword_list.json"
    OUTPUT_PATH = DATA_PATH / "etl/processed/cards/"

    chroma_config = ChromaConfig(**config["CHROMA"])
    db = ChromaDB(chroma_config)

    num_new_cards = update_cards(
        all_cards_file=ALL_CARDS_FILE,
        all_keywords_file=KEYWORD_FILE,
        processed_cards_folder=OUTPUT_PATH,
        db=db,
    )
