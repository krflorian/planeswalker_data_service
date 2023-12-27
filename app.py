import uvicorn

from pathlib import Path
from src.objects import Card, Rule
from src.util import load_config
from src.vector_db import VectorDB

from fastapi import FastAPI
from pydantic import BaseModel, Field
from sentence_transformers import SentenceTransformer

config = load_config(Path("configs/config.yaml"))
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")


class Request(BaseModel):
    text: str
    k: int = Field(default=5)
    threshold: float = Field(default=0.4)
    lasso_threshold: float = Field(default=0.1)


class GetCardsResponse(BaseModel):
    card: Card
    distance: float


class UpdateCardsResponse(BaseModel):
    updated: bool
    number_of_cards: int


db = {
    "card": VectorDB.load(config.get("card_db_file", None)),
    # "rule": VectorDB.load(config.get("rule_db_file", None)),
}


app = FastAPI()


@app.post("/cards/")
async def get_cards(request: Request) -> list[GetCardsResponse]:
    card_db = db["card"]
    query_result = card_db.query(
        text=request.text,
        k=request.k,
        threshold=request.threshold,
        lasso_threshold=request.lasso_threshold,
        model=model,
    )
    return [
        GetCardsResponse(card=result[0], distance=result[1]) for result in query_result
    ]


@app.get("/update_cards/")
async def update_cards() -> UpdateCardsResponse:
    return


@app.post("/rules/")
async def get_rules(request: Request) -> list[Rule]:
    return


if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="debug",
        proxy_headers=True,
        reload=True,
    )
