from pydantic import BaseModel, Field


class Rule(BaseModel):
    text: str
    page: str
    rule_id: str
