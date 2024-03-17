.PHONY: install test requirements

MODULES = common lexer

install:
	python -m pip install -r requirements.txt

test:
	python -m pytest $(foreach module,$(MODULES),--cov=$(module)) --cov-report html

requirements:
	python -m pip freeze > requirements.txt
