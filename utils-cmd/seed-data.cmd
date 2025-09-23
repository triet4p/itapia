@echo off
echo Starting seeding datas...

docker-compose run --it itapia-data-seeds python -m scripts.seed_rules.py
docker-compose run --it itapia-data-seeds python -m scripts.seed_database.py