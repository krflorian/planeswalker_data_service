#%%
from mtg.etl.extractors import ComprehensiveRulesExtractor, RulesGuruExtractor, StackExchangeExtractor, WikipediaExtractor

#%%
extractors = [
    ComprehensiveRulesExtractor(),
    StackExchangeExtractor(),
    WikipediaExtractor(),
    RulesGuruExtractor(),
]

for extractor in extractors:
    extractor.extract_data()
# %%
cr = ComprehensiveRulesExtractor()
cr.extract_data()
# %%
