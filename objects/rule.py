from pydantic import BaseModel, Field
from typing import Optional


class Rule(BaseModel):
    text: str
    rule_id: str
    chapter: str
    subchapter: Optional[str] = None
    examples: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)

    def __len__(self):
        return len(self.text)
