# %%
from pathlib import Path
import re
import random
import os

#os.chdir(r"/home/max/projects/planeswalker_companion")


def load_rules(rules_file=Path("data/raw/rules/MagicCompRules.txt")):
    with open(rules_file, "r") as f:
        text = f.read()
    return text


def extract_rules(text: str) -> list[str]:
    # split the text by the word 'Credits' and take the second part starting with the rules
    text = text.split("Credits", 1)[1]
    # split the text by the word 'Glossary' and take the first part as rules
    rules = text.split("Glossary", 1)[0]
    # split the text by the word 'Glossary' and take the second part as text
    text = text.split("Glossary", 1)[1]
    # split the text by the word 'Credits' and take the first part as glossary_entries
    glossary_entries = text.split("Credits", 1)[0]

    # chunk rules
    rules = re.split(r"(\n\d{3}\.\d+\.)", rules)
    rules = ["".join(x) for x in zip(rules[1::2], rules[0::2])]

    # chunk glossary
    glossary_entries = glossary_entries.split("\n\n")
    glossary_entries = [x for x in glossary_entries if (x != "" and x != "\n")]

    rules = rules + glossary_entries

    print("random rule:")
    print(random.choice(rules))
    print("_________________")

    return rules


# %%

import numpy as np
import openai
import yaml


def get_credentials(credentials_file=Path("config/config.yaml")):
    with open(credentials_file, "r") as infile:
        config = yaml.load(infile, Loader=yaml.FullLoader)
    return config


def get_embeddings(rules: list[str], api_key: str):
    text_embedding = []
    for rule in rules:
        response = openai.Embedding.create(input=rule, model="text-embedding-ada-002")
        print(response)
        embeddings = response["data"][0]["embedding"]
        text_embedding.append((rule, np.array(embeddings)))
    return text_embedding


# %%
import hnswlib
import pickle
from vector_db import VectorDB


def load_vector_db(vector_db_file: Path = Path("data/artifacts/card_vector_db.p")):
    with vector_db_file.open("rb") as infile:
        VectorDB = pickle.load(infile)
    return VectorDB


# %%

# %%
openai.api_key = get_credentials().get("open_ai_token")

text = load_rules(Path("data/raw/rules/MagicCompRules.txt"))
rules = extract_rules(text)
text_embeddings = get_embeddings(rules[1:30], openai.api_key)

with open("data/raw/test", "wb") as fp:  # Pickling
    pickle.dump(text_embeddings, fp)


# %%
with open("data/raw/test", "rb") as fp:  # Unpickling
    text_embeddings = pickle.load(fp)


# %%
def create_graph(
    self,
    labels_and_embeddings: list[tuple[str, np.ndarray]],
    ef: int = 10000,
    M: int = 16,
) -> None:
    """Create the Search Graph.

    Parameters:
        labels_and_embeddings: a list of tuples (label, vector)
        ef: parameter that controls speed/accuracy trade-off during the index construction
        M: parameter that defines the maximum number of outgoing connections in the graph
    """
    # Generating sample data
    if not labels_and_embeddings:
        return
    labels, embeddings = zip(*labels_and_embeddings)
    data = np.array(embeddings)
    ids = np.arange(len(data))

    # Declaring index
    graph = hnswlib.Index(space="cosine", dim=len(data[0]))
    graph.init_index(max_elements=len(embeddings), ef_construction=ef, M=M)
    graph.add_items(data, ids)
    graph.set_ef(ef)

    self.graph = graph
    self.ids_2_labels = {idx: label for idx, label in zip(ids, labels)}


processed_data = [
    card
    for card in idx_2_card_data.values()
    if (card["type_line"] not in BLOCKED_CARD_TYPES) and (card["layout"] == "normal")
]
print(f"saving cards data with {len(processed_data)} cards")
all_cards_file = Path("data/cards/scryfall_all_cards_with_rulings.json")


# %%


vector_db_file = Path("data/artifacts/card_vector_db.p")


vector_db = load_vector_db(vector_db_file=Path("data/artifacts/card_vector_db.p"))

# %%


card_vector_db = VectorDB(
    labels_and_texts=[
        (
            card.name,
            card.to_text(include_price=False, include_rulings=False),
        )
        for card in self.card_name_2_card.values()
    ]
)
