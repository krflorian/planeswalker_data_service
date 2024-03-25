# 
FROM python:3.11

# 
WORKDIR /app

# install dependencies
COPY ./requirements.txt /app
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# copy source code to workingdir 
COPY ./mtg /app/mtg
COPY ./app.py /app/app.py

RUN touch README.md
ARG HF_HOME="app/data/.cache"
ENV HF_HOME="app/data/.cache"

# 
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]