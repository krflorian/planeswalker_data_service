# %%
from pathlib import Path

from mtg.logging import get_logger
from mtg.etl.extractors import (
    RulesGuruExtractor,
    ComprehensiveRulesExtractor,
    StackExchangeExtractor,
    WikipediaExtractor,
)
from mtg.etl.loaders import DocumentLoader

logger = get_logger()

# %%
# setup extractors
DATA_RAW = Path("../data/etl/raw/documents")
DATA_PROCESSED = Path("../data/etl/processed/documents")

rules_guru = RulesGuruExtractor(
    path_data_raw=DATA_RAW / "rulesguru.json",
    path_data_processed=DATA_PROCESSED / "rulesguru.json",
)
comprehensive_rules = ComprehensiveRulesExtractor(
    path_data_raw=DATA_RAW / "comprehensive_rules.txt",
    path_data_processed=DATA_PROCESSED / "comprehensive_rules.json",
)

stack_exchange = StackExchangeExtractor(
    path_data_raw=DATA_RAW / "stackexchange.json",
    path_data_processed=DATA_PROCESSED / "stackexchange.json",
)

wikipedia = WikipediaExtractor(
    path_data_raw=DATA_RAW / "wikipedia.txt",
    path_data_processed=DATA_PROCESSED / "wikipedia.json",
)


extractors = [rules_guru, comprehensive_rules, stack_exchange, wikipedia]

# extractors = [rules_guru]

# %%
# fire extractors

for extractor in extractors:
    extractor.get_data_raw()
    extractor.get_data_processed()


# %%
# setup rules db

rules_db = DocumentLoader(
    path_data_processed=DATA_PROCESSED,
    path_database=Path("../data/artifacts/rules_db_gte.p"),
)
rules_db.load_data()

# %%
