# %%

import time
import logging
from datetime import datetime

logging.basicConfig(filename='../vector_database.log', level=logging.DEBUG,
                    format='%(levelname)s:%(asctime)s:%(message)s')

logger = logging.getLogger()
handler = logging.StreamHandler()  # Create a handler for stdout
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')  # Customize the log format
handler.setFormatter(formatter)

logger.addHandler(handler)  # Add the handler to the logger
logger.setLevel(logging.INFO)  # Set the logging level to INFO

# %%
#Helpers

from pydantic import BaseModel, Field
from typing import Union

import requests

class ChromaDocument(BaseModel):
    id: str  # text for display
    document: str  # text for vectorizing
    metadata: dict[str, Union[str, list[str]]] = Field(
        default_factory=dict
    )  # more info
    
    def __repr__(self):
        return f"Document({self.id})"

def get_request(api_url: str):
    logging.info(f"external request to {api_url}")
    response = requests.get(api_url)
    json = response.json()
    return json

# %%
# Extractor

# extract chapter names
def full_extract() -> list[ChromaDocument]: 
    logging.info(f"Starting full-extraction")
    chapter_names = get_request("https://api.academyruins.com/cr/toc")
    logging.info(f"Successfully extracted chapter names")
    # extract rules
    rules = get_request("https://api.academyruins.com/cr") 
    logging.info(f"Successfully extracted {len(rules)} rules and {len(chapter_names)} chapters")
    
    return rules, chapter_names

    # TODO: get glossary and unoficcial glossary
    # TODO: check how keywords where added to rules


def get_delta(last_update_date: float): # Initialize a set to hold the distinct ruleNumbers 
    logging.info(f"geting delta.")
    updates = get_request(api_url="https://api.academyruins.com/diff/cr")
    distinct_rule_numbers = set()

    if last_update_date < datetime.strptime(updates['creationDay'], "%Y-%m-%d").timestamp():
        # Iterate over each entry in the data
        for entry in updates['changes']:
            try:
                if entry['old'] and 'ruleNumber' in entry['old']:
                    distinct_rule_numbers.add(entry['old']['ruleNumber'])
                if entry['new'] and 'ruleNumber' in entry['new']:
                    distinct_rule_numbers.add(entry['new']['ruleNumber'])

            # Print the distinct ruleNumbers
                
            except Exception as e:
                logging.info(f"Error deleting documents to the collection: {updates['changes']}.")
                continue

        for entry in updates['moves']:
            try:
                distinct_rule_numbers.add(float(entry['from']))
                distinct_rule_numbers.add(float(entry['to']))

            except Exception as e:
                logging.info(f"Error deleting documents to the collection: {updates['moves']}.")
                continue
            
        return sorted(distinct_rule_numbers)

    else: 
        logging.info(f"already up to date: current version: {updates['creationDay']}.")
        return


def delta_extract(ids:list) -> list[ChromaDocument]: 
    logging.info(f"Starting delta-extraction")
    chapter_names = get_request("https://api.academyruins.com/cr/toc")
    logging.info(f"Successfully extracted chapter names")
    # extract rules
    rules = get_request("https://api.academyruins.com/cr") 
    rules = {doc_id: document for doc_id, document in rules.items() if doc_id in ids}
    logging.info(f"Successfully extracted rules")
    return rules, chapter_names

    # TODO: get glossary and unoficcial glossary
    # TODO: check how keywords where added to rules

def transform_data(rules:dict, chapter_names:dict) -> list[ChromaDocument]:
    logging.info(f"Starting transformation")
    # transform rules
    documents = []
    chapters = {}

    for section in chapter_names:
        section_title = section['title']
        for subsection in section['subsections']:
            chapterInfo = {
                "sectionNumber": section['number'],
                "sectionTitle": section['title'],
                "subsectionNumber": subsection['number'],
                "subsectionTitle": subsection['title'],
                "combined_title": f"Comprehensive Rules - {section['number']} {section_title} - {subsection['number']} {subsection['title']}"
            }
            chapters[f'{subsection["number"]}'] = chapterInfo

    for rule in rules.values():
        document = ChromaDocument(
            id = rule['ruleNumber'],
            document = f"{rule['ruleNumber']}: {rule['ruleText']}",
            metadata = {
                "documentType": "rule",
                "sectionNumber": f"{chapters.get(rule['ruleNumber'].split('.')[0])['sectionNumber']}",
                "sectionTitle": str(chapters.get(rule['ruleNumber'].split('.')[0])['sectionTitle']),
                "subsectionNumber": str(chapters.get(rule['ruleNumber'].split('.')[0])['subsectionNumber']),
                "subsectionTitle": str(chapters.get(rule['ruleNumber'].split('.')[0])['subsectionTitle']),
                "combined_title": str(chapters.get(rule['ruleNumber'].split('.')[0])['combined_title']),
                "url": f"https://yawgatog.com/resources/magic-rules/#R{rule['ruleNumber'].replace('.', '')}"
            }
        )
        documents.append(document)

        if rule['examples']:
            example_counter = 1
            for example in rule['examples']:
                document = ChromaDocument(
                    id = f"{rule['ruleNumber']} - Example {example_counter}",
                    document = f"{rule['ruleNumber']} - Example {example_counter}: {example}",
                    metadata = {
                        "documentType": "example",
                        "sectionNumber": str(chapters.get(rule['ruleNumber'].split('.')[0])['sectionNumber']),
                        "sectionTitle": str(chapters.get(rule['ruleNumber'].split('.')[0])['sectionTitle']),
                        "subsectionNumber": str(chapters.get(rule['ruleNumber'].split('.')[0])['subsectionNumber']),
                        "subsectionTitle": str(chapters.get(rule['ruleNumber'].split('.')[0])['subsectionTitle']),
                        "combined_title": f"{chapters.get(rule['ruleNumber'].split('.')[0])['combined_title']} - Example {example_counter}",
                        "url": f"https://yawgatog.com/resources/magic-rules/#R{rule['ruleNumber'].replace('.', '')}"
                    }
                )
                documents.append(document)
                example_counter += 1
    logging.info(f"Successfully transformed data")
    return documents


# %%
# Loader
from chromadb import HttpClient
from chromadb.utils import embedding_functions
from chromadb.api.models.Collection import Collection

def get_collection(
        collection_name:str = 'crRules',
        host:str='localhost', 
        port:int=8000, 
        device:str='cpu',  #possible values: 'cpu', 'cuda'
        model_name:str='thenlper/gte-large'
) -> Collection:
    # create chroma client
    client = HttpClient(host, port)
    #TODO: make other embeddingfunctions available 
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name, device=device)  # sentence-transformers/all-MiniLM-L6-v2
    # get/create collection
    collection = client.get_or_create_collection(name=collection_name, embedding_function=ef)
    logging.info(f"Successfully created collection {collection_name} with {collection.count()} documents")
    return collection



def update_last_successful_load(collection):
    try:
        # write timestamp of last successful load to collection metadata
        collection.modify(metadata={
            "lastUpdate": round(time.time(), 2)
        }) 
        logging.info(f"Successfully updated the last successful load timestamp for {collection.name}.")
    except Exception as e:
        logging.exception(f"Error updating the last successful load timestamp for {collection.name}.")
        raise

def upsert_documents_to_collection(documents: list, collection: list[ChromaDocument]) -> None: 
    try:
        ids = [document.id for document in documents]
        # Upsert documents
        collection.upsert(
            ids=ids, 
            documents=[document.document for document in documents],
            metadatas=[document.metadata for document in documents]
        )
        logging.info(f"Successfully upserted {len(ids)} documents to the collection: {collection.name}.")
    except Exception as e:
        logging.exception(f"Error upserting documents to the collection: {collection.name}.")
        raise
    update_last_successful_load(collection)
    return

def delete_documents_from_collection(collection, ids:list=[]) -> None:
    try:
        collection.delete(ids=ids)
        logging.info(f"Successfully deleted {len(ids)} documents from the collection: {collection.name}.")
    except Exception as e:
        logging.exception(f"Error deleting documents to the collection: {collection.name}.")
        raise
    return

# %%
############ CONFIG ############

chromadb_host:str = 'chromadb'
chromadb_port:str =  '8000'
chromadb_device:str = 'cuda'
model_name:str = 'thenlper/gte-large'
collection_name:str = 'crRulesss'

############ Main ############

collection = get_collection(
    collection_name=collection_name,
    device=chromadb_device
)

if collection.count() == 0:
    rules, chapters = full_extract()
    documents = transform_data(rules, chapters)
    upsert_documents_to_collection(documents, collection)

else:
    ids = get_delta(collection.metadata['lastUpdate'])
    if ids:
        rules, chapters = delta_extract(ids)
        documents = transform_data(rules, chapters)
        upsert_documents_to_collection(documents, collection)

# %%
