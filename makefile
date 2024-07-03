.PHONY: install test requirements clean

modules = lexical syntax langs.a langs.b runtime

install:
	python -m pip install -r requirements.txt

test:
	rm -f benchmark
	python -m pytest -vx $(foreach module,$(modules),--cov=$(module)) --cov-report html
	@echo '[benchmark]'
	@cat benchmark

requirements:
	python -m pip freeze > requirements.txt

clean:
	rm -rf .coverage .pytest_cache htmlcov # delete pytest and coverage caches
	python -Bc "import pathlib; [p.unlink() for p in pathlib.Path('.').rglob('*.py[co]')]" # delete .pyc and .pyo files
	python -Bc "import pathlib; [p.rmdir() for p in pathlib.Path('.').rglob('__pycache__')]" # delete __pycache__ directories
