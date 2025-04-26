# microservice-clothes-store

docker compose -f docker-compose.yml -f docker-compose.auth.yml -f docker-compose.users.yml up


docker compose -f docker-compose.auth.yml run auth-service sh -c "alembic revision --autogenerate -m "init""  
docker compose -f docker-compose.auth.yml run auth-service sh -c "alembic upgrade head"

docker compose -f docker-compose.users.yml run users-service sh -c "alembic revision --autogenerate -m "init""  
docker compose -f docker-compose.users.yml run users-service sh -c "alembic upgrade head"