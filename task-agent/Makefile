.PHONY: test test-live coverage run lint

test:
	python -m pytest tests/ -v

test-live:
	LIVE_API=1 python -m pytest tests/ -v

coverage:
	python -m pytest tests/ -v --cov=. --cov-report=term-missing

run:
	uvicorn api.app:app --reload --host 0.0.0.0 --port 8100

lint:
	python -m py_compile main.py
	python -m py_compile api/app.py
