.PHONY: backend-dev frontend-dev backend-test backend-seed

backend-dev:
	cd backend && uvicorn app.main:app --reload

frontend-dev:
	cd frontend && npm run dev

backend-test:
	cd backend && pytest -q

backend-seed:
	cd backend && python scripts/seed_demo.py
