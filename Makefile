.PHONY: install project build publish package-install lint format setup test clean

install:
	poetry install

setup:
	@mkdir -p data logs
	@if [ ! -f .env ]; then \
		echo "Создаем .env из шаблона..."; \
		cp .env.example .env; \
		echo "⚠️  Отредактируйте .env и добавьте EXCHANGERATE_API_KEY!"; \
	else \
		echo ".env уже существует"; \
	fi

project:
	poetry run project

run:
	python3 main.py

build:
	poetry build

publish:
	poetry publish --dry-run

package-install:
	python3 -m pip install dist/*.whl

lint:
	poetry run ruff check .

format:
	poetry run ruff check . --fix

format-check:
	poetry run ruff format --check .

test:
	poetry run pytest tests/ -v

clean:
	rm -rf dist/ build/ *.egg-info
	rm -rf data/*.json logs/*.log
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

