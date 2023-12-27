from pydantic import BaseModel, Field
from enum import Enum


class RuleType(Enum):
    RULE = "rule"
    GLOSSARY = "glossary"


class Rule(BaseModel):
    text: str
    rule_id: str
    rule_type: str

    def __len__(self):
        return len(self.text)
