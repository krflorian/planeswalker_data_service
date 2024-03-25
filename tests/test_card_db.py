import pytest
from vector_db import VectorDB


@pytest.fixture(scope="module")
def card_db(config):
    card_db = VectorDB.load(config.get("cards_db_file", None))
    return card_db


QUERY_TESTCASES = [
    # only first part of name
    ("What Cards can i add to my chatterfang deck?", "Chatterfang, Squirrel General"),
    # full name, only name
    ("Elesh Norn, Mother of Machines", "Elesh Norn, Mother of Machines"),
    # full name in question
    ("How does Anje Falkenraths ability work?", "Anje Falkenrath"),
    # full name in question
    (
        "What is the strategy for my gandalf the white commander deck?",
        "Gandalf the White",
    ),
    # full name in question
    (
        "What is the strategy for my locust god cedh deck?",
        "The Locust God",
    ),
]


@pytest.mark.parametrize("query,expected_card_name", QUERY_TESTCASES)
def test_card_retrieval(query, expected_card_name, model, card_db):
    """If the card name is in the query the card should be retrieved."""
    # arrange
    maximum_number_of_results = 5

    # act
    response = card_db.query(
        query,
        model=model,
        threshold=0.2,
        k=5,
        lasso_threshold=0.3,
    )
    card_names = [r[0].name for r in response]

    # assert
    assert len(response) <= maximum_number_of_results
    assert expected_card_name in card_names, expected_card_name


def test_card_retrieval_multiple_possible(model, card_db):
    """There are multiple cards with name gandalf - the vector store should return all of them."""
    # arrange
    query = "what cards can i add to my gandalf deck?"
    maximum_number_of_results = 5

    # act
    response = card_db.query(
        query,
        model=model,
        k=maximum_number_of_results,
    )

    # assert
    assert sum(["gandalf" in r[0].name.lower() for r in response]) >= 5
