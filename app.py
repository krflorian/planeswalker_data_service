#%%
from etl import ConfigLoader, RulesExtractor
#%%

config_loader = ConfigLoader()
config = config_loader.get_config()


#%%
extractor_instance = RulesExtractor(config = config).get_data()

