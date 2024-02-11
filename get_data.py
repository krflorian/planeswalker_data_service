#%%
from src.etl import RulesGuru
from src.objects import Document

#%%
rg = RulesGuru()
# %%
rg.from_file()
# %%
rg.data

#%%
rg.process_data()

#%%
from 