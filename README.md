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


## Development 

```shell 
pip install --upgrade poetry 
poetry install 
poetry shell 
```

To build the container download the two necessary huggingface models to data/models: 
- gte-large 
- hallucination_evaluation_model
- bart-large-mnli
