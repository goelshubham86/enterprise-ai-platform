## Run with the active conda environment (ai-assistant).
## Always run `conda activate ai-assistant` before using these targets.

.PHONY: install dev test clean

## Install / sync all dependencies into the active conda env
install:
	pip install -r requirements.txt

## Run the dev server
dev:
	uvicorn app.main:app --reload --port 8000

## Run tests
test:
	pytest

## Remove the legacy .venv if it still exists
clean:
	rm -rf .venv
