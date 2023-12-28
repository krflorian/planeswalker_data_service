# %%
import uvicorn

from pathlib import Path
from src.objects import Card, Rule
from src.util import load_config
from src.vector_db import VectorDB

from fastapi import FastAPI
from pydantic import BaseModel, Field
from sentence_transformers import SentenceTransformer

config = load_config(Path("configs/config.yaml"))
model = SentenceTransformer("thenlper/gte-large")


class Request(BaseModel):
    text: str
    k: int = Field(default=5)
    threshold: float = Field(default=0.4)
    lasso_threshold: float = Field(default=0.1)
    sample_results: bool = Field(default=False)


class GetCardsResponse(BaseModel):
    card: Card
    distance: float


class UpdateCardsResponse(BaseModel):
    updated: bool
    number_of_cards: int


db: dict[str, VectorDB] = {
    "card": VectorDB.load(config.get("cards_db_file", None)),
    "rule": VectorDB.load(config.get("rules_db_file", None)),
}

# %%

app = FastAPI()


@app.post("/cards/")
async def get_cards(request: Request) -> list[GetCardsResponse]:
    if request.sample_results:
        k = request.k * 2
    else:
        k = request.k

    query_result = db["card"].query(
        text=request.text,
        k=k,
        threshold=request.threshold,
        lasso_threshold=request.lasso_threshold,
        model=model,
    )
    if request.sample_results:
        query_result = db["card"].sample_results(query_result, request.k)

    return [
        GetCardsResponse(card=result[0], distance=result[1]) for result in query_result
    ]


@app.post("/rules/")
async def get_rules(request: Request) -> list[Rule]:
    query_result = db["rule"].query(
        text=request.text,
        k=request.k,
        threshold=request.threshold,
        lasso_threshold=request.lasso_threshold,
        model=model,
    )
    rules = []
    for rule, distance in query_result:
        if rule not in rules:
            rules.append(rule)
    return rules


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="debug", proxy_headers=True)
