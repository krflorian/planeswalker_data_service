# %%
import requests

url = "http://127.0.0.1:8000/rules/"

question = "explain deathtouch"
response = requests.post(
    url,
    json={
        "text": question,
        "k": 5,
        "threshold": 0.2,
        "lasso_threshold": 0.02,
        "sample_results": False,
    },
)

print("Question: ", question)
print("Response:")
response.json()

# %%
