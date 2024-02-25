# %%
from src.etl import RulesGuru, Rules, RulesDB
from pathlib import Path

# %%
# Extract RulesGuru Data
rg = RulesGuru()
# rg.extract_data()
rg.data_raw = rg._from_file(Path("../data/etl/raw/documents/rulesguru.json"))
rg.transform_data()

# Extract Rules Data
r = Rules()
r.extract_data()
r.transform_data()

# %%
# Load RulesDB
rdb = RulesDB()
rdb.load_data()
# %%
