from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional


class Rule(BaseModel):
    text: str
    rule_id: str
    chapter: str
    examples: list[str] = Field(default_factory=list)
    subchapter: Optional[str] = None
    keywords: list[str] = Field(default_factory=list)

    def __len__(self):
        return len(self.text)
