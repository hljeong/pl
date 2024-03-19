.PHONY: install test requirements clean

MODULES = common lexer

install:
	python -m pip install -r requirements.txt

test:
	python -m pytest $(foreach module,$(MODULES),--cov=$(module)) --cov-report html

requirements:
	python -m pip freeze > requirements.txt

clean:
	rm -rf htmlcov
	python -Bc "import pathlib; [p.unlink() for p in pathlib.Path('.').rglob('*.py[co]')]"
	python -Bc "import pathlib; [p.rmdir() for p in pathlib.Path('.').rglob('__pycache__')]"
