.PHONY: api api-8001 api-8011 test docker-build docker-run docker-test dev

APP_DIR=📚 Enhanced RAG & Knowledge Graph
APP_MODULE=api.app:app

api:
	uvicorn "$(APP_MODULE)" --app-dir "$(APP_DIR)" --host 127.0.0.1 --port 8000 --reload

api-8001:
	uvicorn "$(APP_MODULE)" --app-dir "$(APP_DIR)" --host 127.0.0.1 --port 8001 --reload

api-8011:
	uvicorn "$(APP_MODULE)" --app-dir "$(APP_DIR)" --host 127.0.0.1 --port 8011 --reload

dev:
	@bash scripts/dev.sh

test:
	@bash -lc 'PYTHONPATH="$(PWD)/$(APP_DIR):$$PYTHONPATH" python -m pytest -q'

smoke:
	@bash scripts/smoke.sh

audit:
	@python scripts/audit_repo.py

docker-build:
	docker build -t ai-stack-enhanced:latest .

docker-run:
	docker run --rm -it -p 8000:8000 -e RAG_API_KEY=secret123 ai-stack-enhanced:latest

docker-test:
	docker run --rm -e PYTHONPATH="/app/$(APP_DIR)" ai-stack-enhanced:latest pytest -q