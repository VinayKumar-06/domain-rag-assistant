.PHONY: setup run ui test lint evaluate

setup:
	python -m venv .venv
	. .venv/bin/activate && python -m pip install -r requirements.txt

run:
	uvicorn app.api.main:app --reload

ui:
	streamlit run ui/streamlit_app.py

test:
	pytest

lint:
	ruff check app ui tests

evaluate:
	python -m evaluation.run
