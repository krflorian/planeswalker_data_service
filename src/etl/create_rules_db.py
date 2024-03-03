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
rules_guru = RulesGuruExtractor(
    path_data_raw=Path("../data/etl/raw/documents/rulesguru.json"),
    path_data_processed=Path("../data/etl/processed/documents/rulesguru.json"),
)
comprehensive_rules = ComprehensiveRulesExtractor(
    path_data_raw=Path("../data/etl/raw/documents/comprehensive_rules.txt"),
    path_data_processed=Path(
        "../data/etl/processed/documents/comprehensive_rules.json"
    ),
)
stack_exchange = StackExchangeExtractor(
    path_data_raw=Path("../data/etl/raw/documents/stackexchange.json"),
    path_data_processed=Path("../data/etl/processed/documents/stackexchange.json"),
)

extractors = [rules_guru, comprehensive_rules, stack_exchange]

# %%
# fire extractors

for extractor in extractors:
    extractor.get_data_raw()
    extractor.get_data_processed()


# %%
# setup rules db

rdb = RulesDB()
rdb.load_data()
