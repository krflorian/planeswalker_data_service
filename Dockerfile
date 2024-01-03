# 
FROM python:3.9
RUN pip install poetry==1.4.2

# 
WORKDIR /app
COPY pyproject.toml poetry.lock app.py ./
COPY ./src /app/src
RUN touch README.md

# 
RUN poetry config virtualenvs.create false
RUN poetry install

# 
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "80"]