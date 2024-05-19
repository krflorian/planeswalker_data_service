# 
FROM python:3.11

# 
WORKDIR /app

# install dependencies
COPY ./requirements.txt /app
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# copy source code to workingdir 
COPY ./etl /app/etl
COPY ./app.py /app/app.py
COPY ./config.yml /app/config.yml

RUN touch README.md
ARG HF_HOME="app/data/.cache"
ENV HF_HOME="app/data/.cache"

CMD ["python", "app.py"]