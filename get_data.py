# %%
from src.etl import RulesGuru, Rules, RulesDB


# %%
# Extract RulesGuru Data

#rg = RulesGuru()
#rg.from_file()
#rg.process_data()

# Extract Rules Data
r = Rules()
r.extract_data()
r.transform_data()

# %%
# Load RulesDB
rdb = RulesDB()
rdb.load_data()
# %%
