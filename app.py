from etl import RulesExtractor, Loader



loader_instance = Loader(
    chromadb_host="localhost",
    chromadb_port="8000",
    chromadb_device="cpu",
    model_name="thenlper/gte-large",
    collection_name="crRulesss"
)

extractor_instance = RulesExtractor(loader_instance)
documents = extractor_instance.get_data()
loader_instance.collection.upsert_documents_to_collection(documents)






if loader_instance.collection.count() == 0:
    documents = extractor_instance.transform_data(full_extract())
    loader_instance.collection.upsert_documents_to_collection(documents)

else:
    documents = extractor_instance.transform_data(delta_extract(loader_instance.collection))
    loader_instance.collection.upsert_documents_to_collection(documents)