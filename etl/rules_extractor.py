import logging
from datetime import datetime
from .chroma_collection import ChromaCollection
from .extractor import Extractor
from .request import get_request
from chromadb.api.models.Collection import Collection
from typing import Optional, List
from pydantic import Field

class RulesExtractor(Extractor):
    collection_name: str = Field('crRules', description="Collection name from ChromaDB")
    rules: Optional[List] = Field(None, description="Collection object from ChromaDB")
    chapter_names: Optional[List] = Field(None, description="Collection object from ChromaDB")


    def get_data(self):
        updates = get_request(api_url="https://api.academyruins.com/diff/cr")

        if self.loader.collection.count() == 0 or self.config["ETL_MODE"] == 'full':
            self.full_extract()
        elif self.loader.collection.metadata['lastUpdate'] < datetime.strptime(updates['creationDay'], "%Y-%m-%d").timestamp():
            self.delta_extract()
        else: 
            print(f"collection {self.loader.collection_name} is up-to-date with latest data from {updates['creationDay']}")
            return

        self.transform_data()
        self.loader.upsert_documents_to_collection(self.documents)
        return

# extract chapter names
    def full_extract(self) -> list[ChromaCollection]: 
        logging.info(f"Starting full-extraction")
        self.chapter_names = get_request("https://api.academyruins.com/cr/toc")
        logging.info(f"Successfully extracted chapter names")
        # extract rules
        self.rules = get_request("https://api.academyruins.com/cr") 
        logging.info(f"Successfully extracted {len(self.rules)} rules and {len(self.chapter_names)} chapters")


        # TODO: get glossary and unoficcial glossary
        # TODO: check how keywords where added to rules


    def get_delta(self): # Initialize a set to hold the distinct ruleNumbers 
        logging.info(f"geting delta.")
        updates = get_request(api_url="https://api.academyruins.com/diff/cr")
        distinct_rule_numbers = set()

        if self.loader.collection.metadata['lastUpdate'] < datetime.strptime(updates['creationDay'], "%Y-%m-%d").timestamp():
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
                
            return sorted(self.distinct_rule_numbers)

        else: 
            logging.info(f"already up to date: current version: {updates['creationDay']}.")
            return


    def delta_extract(self, collection:Collection) -> list[ChromaCollection]: 
        ids = self.get_delta(collection)
        if ids:
            logging.info(f"Starting delta-extraction")
            self.chapter_names = get_request("https://api.academyruins.com/cr/toc")
            logging.info(f"Successfully extracted chapter names")
            # extract rules
            rules = get_request("https://api.academyruins.com/cr") 
            self.rules = {doc_id: document for doc_id, document in rules.items() if doc_id in ids}
            logging.info(f"Successfully extracted {len(self.rules)} rules")


    def transform_data(self) -> list[ChromaCollection]:
        logging.info(f"Starting transformation")
        # transform rules
        documents = []
        chapters = {}

        for section in self.chapter_names:
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

        for rule in self.rules.values():
            document = ChromaCollection(
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
                    document = ChromaCollection(
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
        
        self.documents = documents
        logging.info(f"Successfully transformed data")


