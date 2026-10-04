.PHONY: install lint test run site docker

install:
	pip install -r requirements-dev.txt

lint:
	ruff check .
	ruff format --check .

test:
	pytest --cov=app --cov-report=term-missing --cov-report=xml:coverage.xml \
		--cov-report=html:htmlcov --junitxml=junit.xml

run:
	uvicorn app.main:app --reload

site: test
	python scripts/build_site.py

docker:
	docker build --build-arg GIT_SHA=$$(git rev-parse --short HEAD) -t pipelinelab:local .
