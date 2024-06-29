.PHONY: install test requirements clean

modules = lexical syntax langs.a langs.b

install:
	python -m pip install -r requirements.txt

test:
	python -m pytest -x $(foreach module,$(modules),--cov=$(module)) --cov-report html

requirements:
	python -m pip freeze > requirements.txt

clean:
	rm -rf .coverage .pytest_cache htmlcov # delete pytest and coverage caches
	python -Bc "import pathlib; [p.unlink() for p in pathlib.Path('.').rglob('*.py[co]')]" # delete .pyc and .pyo files
	python -Bc "import pathlib; [p.rmdir() for p in pathlib.Path('.').rglob('__pycache__')]" # delete __pycache__ directories
