venv:
	@test -d .venv || python -m venv .venv

install: venv
	pip install -r requirements.txt

test:
	pytest tests/

lint:
	flake8 srcs/ tests/

format:
	black srcs/ tests/

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf .pytest_cache .mypy_cache dist build *.egg-info
