from pathlib import Path
from pydantic import BaseModel, Field
from uuid import uuid4
from .document import Document


def create_id():
    return str(uuid4())


class Card(BaseModel):
    name: str
    mana_cost: str
    type: str
    oracle: str
    price: float
    url: str
    power: str = "None"
    toughness: str = "None"
    id: str = Field(default_factory=create_id)
    color_identity: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    rulings: list[Document] = Field(default_factory=list)
    legalities: dict[str, str] = Field(default_factory=dict)
    categories: list[str] = Field(default_factory=list)
    _image: Path = None

    def __repr__(self) -> str:
        return f"Card({self.name})"

    def to_dict(self) -> dict:
        data = self.__dict__
        data["rulings"] = [
            ruling.__dict__ if not isinstance(ruling, dict) else ruling
            for ruling in self.rulings
        ]
        return data

    def to_chroma(self) -> dict[str, str]:
        data = {
            "name": self.name,
            "power": self.power,
            "toughness": self.toughness,
        }
        for color_identity in self.color_identity:
            data[f"color_identity_{color_identity}"] = True

        for keyword in self.keywords:
            data[f"keyword_{keyword}"] = True

        for legality in self.legalities:
            if self.legalities[legality] == "legal":
                data[f"{legality}_legal"] = True

        return data

    def to_text(self, include_price: bool = True):
        """parse card data to text format"""
        text = []
        text.append(self.name)
        text.append(f"type: {self.type}")
        text.append(f"cost: {self.mana_cost}")
        if (self.power != "0") and (self.toughness != "0"):
            text.append(f"power/toughness: {str(self.power)}/{str(self.toughness)}")
        if self.keywords:
            text.append("keywords: " + " ".join(self.keywords))
        if self.color_identity:
            text.append("color identity: " + " ".join(self.color_identity))
        text.append(self.oracle)

        # price
        if include_price:
            if self.price != 0.0:
                text.append(f"price in EUR: {self.price}")

        return "\n".join(text)
