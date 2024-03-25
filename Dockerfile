# 
FROM python:3.11

# 
WORKDIR /app

COPY pyproject.toml poetry.lock README.md ./
COPY app.py requirements.txt ./
RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY ./src /app/src
RUN pip install . 

RUN touch README.md
ARG HF_HOME="app/data/.cache"
ENV HF_HOME="app/data/.cache"

# 
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]