# %%
from src.etl import RulesGuru, Rules, RulesDB
from pathlib import Path

#%%
# Extract RulesGuru Data
rg = RulesGuru()
rg.get_data_raw()
#rg.data_raw = rg._from_file(Path("../data/etl/raw/documents/rulesguru.json.bak"))
rg.get_data_processed()

# Extract Rules Data
r = Rules()
r.get_data_raw()
r.get_data_processed()

# Load RulesDB
rdb = RulesDB()
rdb.load_data()