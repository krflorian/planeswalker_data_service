#%%
from etl import ConfigLoader, RulesExtractor, GlossaryExtractor
#%%

config_loader = ConfigLoader()
config = config_loader.get_config()


#%%

extractors = [
    RulesExtractor(config = config),
    GlossaryExtractor(config = config)
]

for extractor in extractors:
    extractor.get_data()



# %%
extractors[0].loader.collection.get(where={"documentType" : "glossary"})
# %%
