import pytest
from src.vector_db import VectorDB


@pytest.fixture(scope="module")
def rules_db(config):
    rules_db: VectorDB = VectorDB.load(config.get("rules_db_file", None))
    return rules_db


# tests
TEST_CASES_KEYWORDS = [
    # deaththouch
    (
        "what happens if i attack with a 1/1 deathtouch creature and my opponent blocks with a 2/2 token?",
        ["702.2b", "702.2c"],
    ),
    # first strike
    (
        "what happens if i attack with a 1/1 first strike creature and my opponent blocks with a 3/1 creature?",
        ["702.7b", "702.4b"],
    ),
    # trample
    (
        "what happens if i attack with a 5/5 creature with trample and my opponent blocks with a 1/1 creature?",
        ["702.19b"],
    ),
    # deathtouch and trample
    (
        "what happens if i attack with a 5/5 creature with trample and my opponent blocks with a 1/1 creature with deathtouch?",
        ["702.19b", "702.2b", "702.2c"],  # TODO does not find deathtouch
    ),
    # myriad
    (
        "what happens when i attack with a creature with myriad",
        ["Myriad", "702.116a", "702.116b"],
    ),
    # forest walk
    ("explain forest walk", ["Forestwalk"]),
]


@pytest.mark.parametrize("question,expected_rule_ids", TEST_CASES_KEYWORDS)
def test_rule_db_keyword_retrieval(
    question: str, expected_rule_ids: list[str], model, rules_db
):
    # act
    results = rules_db.query(
        question, model=model, k=5, threshold=0.2, lasso_threshold=0.02
    )
    rule_ids = [rule.rule_id for rule, distance in results]

    # assert
    assert all([expected_rule_id in rule_ids for expected_rule_id in expected_rule_ids])
