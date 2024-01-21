# 
FROM python:3.11
#RUN pip install poetry==1.4.2

# 
WORKDIR /app

#COPY pyproject.toml poetry.lock app.py ./
COPY app.py requirements.txt ./
RUN pip install -r requirements.txt

COPY ./src /app/src
RUN touch README.md
ARG HF_HOME="app/data/.cache"
ENV HF_HOME="app/data/.cache"

# 
#RUN poetry config virtualenvs.create false
#RUN poetry install
#RUN pip install . 

# 
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]