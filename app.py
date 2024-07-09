# %%

import uvicorn
from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel, Field
from sentence_transformers import SentenceTransformer, CrossEncoder

from mtg.objects import Card, Document
from mtg.vector_db import VectorDB
from mtg.util import load_config
from mtg.hallucination import validate_answer

config: dict = load_config(Path("configs/config.yaml"))
vector_model: SentenceTransformer = SentenceTransformer(
    config.get("vector_model_name", "thenlper/gte-large")
)
hallucination_model: CrossEncoder = CrossEncoder(
    config.get("halucination_model_name", "vectara/hallucination_evaluation_model")
)

db: dict[str, VectorDB] = {
    "card": VectorDB.load(config.get("cards_db_file", None)),
    "rule": VectorDB.load(config.get("rules_db_file", None)),
}

db["card"]

# %%
app = FastAPI()


# Interface
## Rules
class RulesRequest(BaseModel):
    text: str
    k: int = Field(default=5)
    threshold: float = Field(default=0.2)
    lasso_threshold: float = Field(default=0.02)


class GetRulesResponse(BaseModel):
    document: Document
    distance: float


## Cards
class CardsRequest(BaseModel):
    text: str
    k: int = Field(default=5)
    threshold: float = Field(default=0.4)
    lasso_threshold: float = Field(default=0.1)
    sample_results: bool = Field(default=False)


class GetCardsResponse(BaseModel):
    card: Card
    distance: float


## Parse Text
class ParseTextRequest(BaseModel):
    text: str


class ParseTextResponse(BaseModel):
    text: str
    cards: list[Card]


# Routes
@app.post("/cards/")
async def get_cards(request: CardsRequest) -> list[GetCardsResponse]:
    # when sampling retrieve more cards
    if request.sample_results:
        k = request.k * 2
    else:
        k = request.k

    # query database
    query_result = db["card"].query(
        text=request.text,
        k=k,
        threshold=request.threshold,
        lasso_threshold=request.lasso_threshold,
        model=vector_model,
    )
    if request.sample_results:
        query_result = db["card"].sample_results(query_result, request.k)

    return [
        GetCardsResponse(card=result[0], distance=result[1]) for result in query_result
    ]


@app.post("/rules/")
async def get_rules(request: RulesRequest) -> list[GetRulesResponse]:
    # query database
    query_result = db["rule"].query(
        text=request.text,
        k=request.k,
        threshold=request.threshold,
        lasso_threshold=request.lasso_threshold,
        model=vector_model,
    )
    # filter unique documents
    documents = []
    for doc, distance in query_result:
        if doc not in documents:
            documents.append((doc, distance))
    return [
        GetRulesResponse(document=doc, distance=distance) for doc, distance in documents
    ]


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="debug", proxy_headers=True)
