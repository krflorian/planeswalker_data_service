# %%
from src.vector_db import VectorDB
import time
from sentence_transformers import SentenceTransformer

model = SentenceTransformer(
    "thenlper/gte-large"
)  # thenlper/gte-large   sentence-transformers/all-MiniLM-L6-v2
model


# %%
import json

with open("data/scryfall_all_cards_with_rulings.json", "r", encoding="utf-8") as infile:
    data = json.load(infile)

len(data)

# %%
from src.objects import Card

all_cards = []
for card_data in data:
    all_cards.append(
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
            rulings=card_data.get("rulings", []),
        )
    )

len(all_cards)

# %%

# all_cards = all_cards[:100]
texts, cards = [], []
for card in all_cards:
    texts.append(card.to_text(include_price=False, include_rulings=False))
    cards.append(card)


card_db = VectorDB(
    texts=texts,
    data=cards,
    model=model,
)


# %%

QUERY_TESTCASES = [
    ("What Cards can i add to my chatterfang deck?", "Chatterfang, Squirrel General"),
    ("Elesh Norn, Mother of Machines", "Elesh Norn, Mother of Machines"),
    ("How does Anje Falkenraths ability work?", "Anje Falkenrath"),
    (
        "What is the strategy for my gandalf the white commander deck?",
        "Gandalf the White",
    ),
    (
        "What is the strategy for my locust god cedh deck?",
        "The Locust God",
    ),
]
maximum_number_of_results = 10
responses = []
for query, expected_card_name in QUERY_TESTCASES:
    start = time.time()
    response = card_db.query(
        query,
        model=model,
        threshold=0.2,
        k=maximum_number_of_results,
        lasso_threshold=0.3,
    )
    responses.append((response, expected_card_name))
    print(f"runtime {time.time()-start:.2f}")
    # print(expected, [c for c in all_cards if expected in c.name.lower()])

    assert len(responses) <= maximum_number_of_results
    assert expected_card_name in [r[0].name for r in response], expected_card_name


# %%
from pathlib import Path

db_name = "card_db_gte"
card_db_file = Path(f"data/{db_name}.p")
card_db.dump(card_db_file)

# %%

response = card_db.query(
    "What card can i add to my gandalf commander deck? ",
    model=model,
    threshold=0.8,
    k=maximum_number_of_results,
    lasso_threshold=0.3,
)
response


# %%

from src.vector_db import VectorDB

test = VectorDB.load(f"data/{db_name}.p")
test

# %%
