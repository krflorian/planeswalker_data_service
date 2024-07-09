import os
from langchain_openai import ChatOpenAI
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.utils.function_calling import convert_to_openai_function


PROMPT = """You are a Magic the Gathering Expert and Deckbuilding advisor.
Categorize the following Card: 
{card_text}
"""


class MTGCardCategories(BaseModel):
    """Categorize a Magic: The Gathering card with boolean attributes."""

    aggro: bool = Field(
        False,
        description="Indicates if the card is aggressive and applies early game pressure.",
    )
    buff: bool = Field(
        False,
        description="Indicates if the card provides a buff or enhancement to creatures or other permanents.",
    )
    debuff: bool = Field(
        False,
        description="Indicates if the card weakens or hinders opponents' creatures or permanents.",
    )
    card_draw: bool = Field(
        False, description="Indicates if the card allows you to draw additional cards."
    )
    combo_piece: bool = Field(
        False,
        description="Indicates if the card is part of a combo that can lead to a game-winning scenario.",
    )
    control: bool = Field(
        False,
        description="Indicates if the card is used to control the game state, often by neutralizing threats.",
    )
    counterspell: bool = Field(
        False,
        description="Indicates if the card can counter or negate opponents' spells.",
    )
    burn: bool = Field(
        False,
        description="Indicates if the card deals direct damage to creatures, players, or planeswalkers.",
    )
    discard: bool = Field(
        False,
        description="Indicates if the card forces opponents to discard cards from their hand.",
    )
    graveyard_interaction: bool = Field(
        False,
        description="Indicates if the card interacts with the graveyard, such as retrieving cards or triggering effects based on graveyard contents.",
    )
    protection: bool = Field(
        False,
        description="Indicates if the card provides protection or makes permanents harder to remove.",
    )
    ramp: bool = Field(
        False,
        description="Indicates if the card accelerates your mana production, allowing you to play more powerful cards earlier.",
    )
    removal: bool = Field(
        False,
        description="Indicates if the card can remove creatures, artifacts, enchantments, or other permanents from the battlefield.",
    )
    sacrifice: bool = Field(
        False,
        description="Indicates if the card involves sacrificing your own creatures or permanents for a beneficial effect.",
    )
    token_generation: bool = Field(
        False,
        description="Indicates if the card creates token creatures or other token permanents.",
    )
    tutor: bool = Field(
        False,
        description="Indicates if the card allows you to search your library for specific cards.",
    )
    utility: bool = Field(
        False,
        description="Indicates if the card provides versatile benefits that can fit various situations.",
    )
    win_condition: bool = Field(
        False,
        description="Indicates if the card provides a direct path to victory, often through an alternate win condition or overwhelming power.",
    )


def create_categorizer(model_name: str = "gpt-4o"):
    llm = ChatOpenAI(
        model=model_name,
        temperature=0.001,
        n=1,
    )
    llm_with_functions = llm.bind(
        functions=[convert_to_openai_function(MTGCardCategories)],
        function_call={"name": "MTGCardCategories"},
    )

    prompt = ChatPromptTemplate.from_template(PROMPT)

    chat = prompt | llm_with_functions
    return chat
