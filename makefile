

run: 
	docker compose --profile dev up --remove-orphans

test: 
	docker compose --profile test up --remove-orphans
	 