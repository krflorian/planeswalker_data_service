import logging
import uvicorn
from pathlib import Path
from typing import Optional
import difflib

from fastapi import FastAPI
from pydantic import BaseModel, Field

from mtg.objects import Card, Document
from mtg.chroma.config import ChromaConfig
from mtg.chroma.chroma_db import ChromaDB, CollectionType
from mtg.util import load_config, read_json_file
from mtg.url_parsing import parse_card_names

config: dict = load_config(Path("configs/config.yaml"))
chroma_config = ChromaConfig(**config["CHROMA"])
db = ChromaDB(chroma_config)

cards_collection = db.get_collection(CollectionType.CARDS)
documents_collection = db.get_collection(CollectionType.DOCUMENTS)


# load card data
# TODO -> make class CardDB and load from config
cards_folder = Path(config.get("cards_folder", "../data/etl/processed/cards"))
data = []
for file in cards_folder.iterdir():
    data.append(read_json_file(file))

cards = [Card(**d) for d in data]
card_name_2_card = {card.name: card for card in cards}
all_card_names = list(card_name_2_card)

all_keywords, all_legalities = set(), set()

for card in data:
    for keyword in card["keywords"]:
        all_keywords.add(keyword)
    for legality in card["legalities"]:
        if card["legalities"][legality] == "legal":
            all_legalities.add(legality)

all_keywords = list(all_keywords)
all_legalities = list(all_legalities)
all_color_identities = {"W", "U", "B", "R", "G"}
logging.info(f"loaded {len(cards)} cards")


# load rules data
docs_folder = Path(config.get("documents_folder", "../data/etl/processed/documents"))
documents = []
for file in docs_folder.iterdir():
    data = read_json_file(file)
    for doc in data:
        documents.append(Document(**doc))
document_name_2_document = {doc.name: doc for doc in documents}
logging.info(f"loaded {len(documents)} documents")

# app
app = FastAPI()


# Interface
## Rules
class RulesRequest(BaseModel):
    text: str
    k: int = Field(default=5)
    threshold: float = Field(default=0.2)


class GetRulesResponse(BaseModel):
    document: Document
    distance: float


## Cards
class CardsRequest(BaseModel):
    text: str
    keywords: list[str] = Field(default_factory=list)
    color_identity: list[str] = Field(default_factory=list)
    legality: Optional[str] = Field(default=None)
    k: int = Field(default=20)
    threshold: float = Field(default=0.4)


class GetCardsResponse(BaseModel):
    card: Card
    distance: float


class CardNameRequest(BaseModel):
    card_name: str


class CardParseRequest(BaseModel):
    text: str


class CardParseResponse(BaseModel):
    text: str


# Routes
@app.get("/card_name/{card_name}")
async def search_card(card_name: str) -> GetCardsResponse:

    card = card_name_2_card.get(card_name, None)
    if card is None:
        card_names = difflib.get_close_matches(card_name, all_card_names, n=1)
        card = card_name_2_card.get(card_names[0], None)
    if card is None:
        raise ValueError(f"Card Name not found - {card_name}")
    return GetCardsResponse(card=card, distance=0.0)


@app.post("/parse_card_urls/")
async def parse_cards(request: CardParseRequest) -> CardParseResponse:

    text = parse_card_names(request.text, card_name_2_card=card_name_2_card)
    return CardParseResponse(text=text)


@app.post("/cards/")
async def get_cards(request: CardsRequest) -> list[GetCardsResponse]:
    # TODO sampling
    # TODO code should be in class CardDB
    # create query
    query = {"query_texts": [request.text], "n_results": request.k, "where": {}}

    # keywords
    for search_term in request.keywords:
        matches = difflib.get_close_matches(search_term, all_keywords, n=1)
        if matches:
            query["where"][f"keyword_{matches[0]}"] = True
        else:
            logging.info(f"did not find keyword: {query}")

    # legalities
    if request.legality is not None:
        matches = difflib.get_close_matches(request.legality, all_legalities, n=1)
        if matches:
            query["where"][f"{matches[0]}_legal"] = True
        else:
            logging.info(f"did not find legality: {query}")

    # color identity
    for color in request.color_identity:
        if color.upper() in all_color_identities:
            query["where"][f"color_identity_{color.upper()}"] = True

    if len(query["where"]) > 1:
        query["where"] = {
            "$and": [{key: value} for key, value in query["where"].items()]
        }

    # query
    results = cards_collection.query(**query)

    response = []
    for distance, metadata in zip(results["distances"][0], results["metadatas"][0]):
        if distance <= request.threshold:
            response.append(
                GetCardsResponse(
                    card=card_name_2_card.get(metadata["name"], None), distance=distance
                )
            )

    return response


@app.post("/rules/")
async def get_rules(request: RulesRequest) -> list[GetRulesResponse]:

    query = {"query_texts": [request.text], "n_results": request.k}
    results = documents_collection.query(**query)

    response = []
    for distance, metadata in zip(results["distances"][0], results["metadatas"][0]):
        if distance <= request.threshold:
            response.append(
                GetRulesResponse(
                    document=document_name_2_document.get(metadata["name"], None),
                    distance=distance,
                )
            )

    return response


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="debug", proxy_headers=True)
