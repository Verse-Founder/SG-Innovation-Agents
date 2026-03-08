.PHONY: run test test-live coverage

run:
	cd /Users/weichayi/Desktop/SG-Innovation-Agents/to-doctor-agent && \
	uvicorn api.app:app --host 0.0.0.0 --port 8200 --reload

test:
	cd /Users/weichayi/Desktop/SG-Innovation-Agents/to-doctor-agent && \
	python -m pytest tests/ -v --tb=short

test-live:
	cd /Users/weichayi/Desktop/SG-Innovation-Agents/to-doctor-agent && \
	LIVE_API=1 python -m pytest tests/ -v --tb=short

coverage:
	cd /Users/weichayi/Desktop/SG-Innovation-Agents/to-doctor-agent && \
	python -m pytest tests/ --cov=. --cov-report=html -v
