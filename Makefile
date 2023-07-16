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
	python3 src/examples/shell_example.py -h > docs/source/modules/shell_help.txt
	cd docs && yes y | make sphinx-quickstart
	cd docs && make html

make html:
	cd docs && sphinx-apidoc -o source/modules ../src/mash
	cd docs && make html

docs-generate:
	cd docs && make html
	make docs-show

docs-show:
	open docs/build/html/index.html

docs-watch:
	find docs/source -type f -name '*.rst' -o -name '*.md' -prune -o -name 'docs/source/modules/*.rst' | entr make html

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

