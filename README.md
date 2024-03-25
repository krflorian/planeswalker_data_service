# Planeswalker Data Service  

This is an API build for [Nissa](https://github.com/krflorian/planeswalker_companion). 
The Service uses FASTAPI and HNSWLIB to query cards data and rules regarding `Magic: The Gathering`. 

## USAGE  

1.  Start the Server 
```shell 
uvicorn app:app
```

2. Look at the Interfaces and Try out the Service  
http://127.0.0.1:8000/docs

## SETUP

At the moment there are two Vector Databases that have to be filled before the dataservice can start workting. 

1. Rules DB 
    - includes data relevant for understanding the game:
    - [Comprehensive Rulebook](https://magic.wizards.com/en/rules)
    - [Data about Keywords](https://en.wikipedia.org/wiki/List_of_Magic:_The_Gathering_keywords)
    - Question Answer pairs from [RulesGuru](https://rulesguru.net/)  
    - Question Answer pairs from [Stackoverflow](https://boardgames.stackexchange.com/questions/tagged/magic-the-gathering)

2. Cards DB 
    - includes all mtg card data from [scryfall](https://scryfall.com/docs/api/bulk-data)

To fill the database there are scripts in the folder `src/etl` every script beginning with `create_` will create data as json files that can then be vectorized and inserted in the corresponding database. For vectorizing the data at the moment we are using the opensouce model [gte-large](https://huggingface.co/thenlper/gte-large) from huggingface.

To speed up vectorization the model can be placed on gpu. 

https://docs.rapids.ai/install
```shell 
conda create --solver=libmamba -n rapids-24.04 -c rapidsai-nightly -c conda-forge -c nvidia  \
    python=3.11 cuda-version=12.0 \
    pytorch
conda init 
conda activate rapids-24.04

poetry shell 
python src/etl/create_card_db.py
```

## Development 

```shell 
pip install --upgrade poetry 
poetry install 
poetry shell 
```

To build the container download the three necessary huggingface models to data/models: 
- gte-large 
- hallucination_evaluation_model
- bart-large-mnli

