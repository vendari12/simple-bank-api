setup:
	docker compose up db -d
# wait for postgres to startup
	sleep 2
	docker exec -i banking-db psql -U banking -d postgres < ./postgres/create_db.sql


run: setup
	docker compose --profile dev up --remove-orphans

test:
	docker compose up test-db -d
# wait for postgres to startup
	sleep 2
	docker exec -i banking-test-db psql -U banking -d postgres < ./postgres/create_db.sql
	docker compose --profile test up --remove-orphans
	 