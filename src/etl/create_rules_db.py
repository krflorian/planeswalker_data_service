# %%
from src.etl.extractors import (
    RulesGuruExtractor,
    ComprehensiveRulesExtractor,
    StackExchangeExtractor,
)
from src.etl.loaders.data_loader import RulesDB
from pathlib import Path

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


# extractors = [rules_guru, comprehensive_rules, stack_exchange]

extractors = [stack_exchange]

# %%
# fire extractors

for extractor in extractors:
    extractor.get_data_raw()
    extractor.get_data_processed()


# %%
# setup rules db

rdb = RulesDB()
rdb.load_data()
