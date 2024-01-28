# %%
import random
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


# %%

if __name__ == "__main__":
    # create variables
    CARDS_DATA_PATH = Path("../data/cards")

    # load model
    model = SentenceTransformer("../data/models/gte-large")

    # load data
    data = download_card_data()

    # save data
    data_sample = random.choices(data, k=10)
    save_card_data(
        data=data,
        all_cards_file=CARDS_DATA_PATH / "scryfall_all_cards_with_rulings.json",
    )
    save_card_data(
        data=data_sample,
        all_cards_file=CARDS_DATA_PATH / "scryfall_all_cards_with_rulings_sample.json",
    )
