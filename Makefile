.PHONY: docs

test:
	# print difference as a warning
	autopep8 -r --diff .
	flake8 --ignore=E241,E501,W504
	pytest -n 4

format:
	autopep8 -r -a -a -a --in-place .

clean:
	find . -name '__pycache__' | xargs rm -rf {1}
	#find . -name '__pycache__' -exec rm -rf {} \;
	rm -rf dist
	rm -rf src/*.egg-info

setup:
	pip3 install -r requirements.txt

install:
	python3 -m pip install .

build:
	make clean
	python3 -m build

upload-test:
	make build
	python3 -m twine upload --repository testpypi dist/* -u "${user}" -p "${pass}"

upload:
	make build
	python3 -m twine upload dist/* -u "${user}" -p "${pass}"

docs-init:
	mkdir -p docs
	cd docs && yes y | make sphinx-quickstart
	make docs

docs:
	cd docs && sphinx-apidoc -o source/modules ../src/mash
	python3 src/examples/shell_example.py -h > docs/source/modules/shell_help.txt
	cd docs && make html

docs-show:
	open docs/build/html/index.html

docs-watch:
	make docs-show
	find docs/source -type f -name '*.rst' -o -name '*.md' -prune -o -name 'docs/source/modules/*.rst' | entr make docs

docs-clean:
	rm -rf docs/source/modules
	rm -rf docs/build

pydocs:
	cd src && pydoc -b

tree:
	tree src -L 2 -d
	tree src/mash -L 2 --gitignore -I '_*|*.out'

ast:
	egrep -rh '^class \w+(\(\w+\))?\:' src/mash/shell/ast

web:
	open web/home.html
	python3 src/examples/server.py

