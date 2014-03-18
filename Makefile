help:
	@echo "clean-pyc - remove Python file artifacts"
	@echo "lint - check style with flake8"
	@echo "update_reqs - update all requirements in requirements.txt"
	@echo "upgrade_packages - upgrade all installed packages with pip"
	@echo "test - run tests"
	@echo "coverage - check code coverage quickly with the default Python"

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +

lint:
	find . -iname "*.py" | xargs flake8

update_reqs:
	pip install -U -r requirements.txt

upgrade_packages:
	pip freeze --local | grep -v "^\-e" | cut -d = -f 1  | xargs pip install -U

test:
	clear; nosetests -s --exe --cover-erase --with-coverage --cover-package=releaseunpacker

coverage:
	clear; nosetests --exe --cover-erase --with-coverage --cover-package=releaseunpacker
	coverage html releaseunpacker/releaseunpacker.py
	open htmlcov/index.html
