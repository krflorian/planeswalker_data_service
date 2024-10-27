# Planeswalker Data Service  

This is an API build for [Nissa](https://github.com/krflorian/planeswalker_companion). 
The Service uses FASTAPI and HNSWLIB to query cards data and rules regarding `Magic: The Gathering`. 

## USAGE  

1.  Start the Server 
```shell 
fastapi run app.py
```

2. Look at the Interfaces and Try out the Service  
http://127.0.0.1:8000/docs

## SETUP

At the moment there are two Vector Databases that have to be filled before the dataservice can start working. 

1. Rules DB 
    - includes data relevant for understanding the game:
    - [Comprehensive Rulebook](https://magic.wizards.com/en/rules)
    - [Data about Keywords](https://en.wikipedia.org/wiki/List_of_Magic:_The_Gathering_keywords)
    - Question Answer pairs from [RulesGuru](https://rulesguru.net/)  
    - Question Answer pairs from [Stackoverflow](https://boardgames.stackexchange.com/questions/tagged/magic-the-gathering)

2. Cards DB 
    - includes all mtg card data from [scryfall](https://scryfall.com/docs/api/bulk-data)

To fill the database there are scripts in the folder `src/etl` every script beginning with `create_` will create data as json files that can then be vectorized and inserted in the corresponding database. For vectorizing the data at the moment we are using the opensouce model [gte-large](https://huggingface.co/thenlper/gte-large) from huggingface.

## Development 

```shell 
pip install --upgrade poetry 
poetry install 
poetry shell 
```

