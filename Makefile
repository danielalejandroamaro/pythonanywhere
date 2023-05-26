init-migration:
	alembic init alembic

migration-create:
	alembic revision -m "better contrains on facture"

migration-update:
	alembic upgrade head

migration-autogenerate:
	alembic revision --autogenerate -m "database add ProcessQueue"

migration-downgrade:
	alembic downgrade -1

run-app:
	uvicorn main:app --host 0.0.0.0 --port 8000 --reload
