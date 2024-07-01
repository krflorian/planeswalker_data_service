poetry export --without-hashes --format=requirements.txt > requirements.txt
docker compose rm -f nissa-etl
docker rmi nissa-etl
docker compose build app
docker compose up app