#%%
from mtg.etl.extractors import ComprehensiveRulesExtractor, RulesGuruExtractor, StackExchangeExtractor, WikipediaExtractor

#%%
extractors = [
    ComprehensiveRulesExtractor(),
    RulesGuruExtractor(),
    StackExchangeExtractor(),
    WikipediaExtractor
]

for extractor in extractors:
    extractor.extract_data()
# %%
