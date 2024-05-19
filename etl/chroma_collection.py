from pydantic import BaseModel, Field
from typing import Union

class ChromaCollection(BaseModel):
    id: str  # text for display
    document: str  # text for vectorizing
    metadata: dict[str, Union[str, list[str]]] = Field(
        default_factory=dict
    )  # more info
    
    def __repr__(self):
        return f"Document({self.id})"