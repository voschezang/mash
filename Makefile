.PHONY: docs web test

github = https://github.com/voschezang/mash/blob/main/
out = docs/source/modules

test:
	# print difference as a warning
	autopep8 -r --diff src
	#flake8 --ignore=E241,E501,W504 src
	make lint
	pytest -n 4

lint:
	# remove auto-generated file
	rm -f src/mash/shell/grammer/parsetab.py
	# enforce linting
	flake8 src --count --select=E9,F63,F7,F82 --show-source --statistics
	# show lenient errors
	flake8 src --count --exit-zero --max-complexity=11 --max-line-length=127 --statistics

format:
	autopep8 -r -a -a -a --in-place src/mash

clean:
	rm -f src/mash/shell/grammer/parsetab.py
	find . -name '__pycache__' | xargs rm -rf {1}
	#find . -name '__pycache__' -exec rm -rf {} \;
	rm -rf dist
	rm -rf src/*.egg-info
	make docs-clean

setup:
	pip3 install -r requirements.txt
	pip3 install -r build_requirements.txt

install:
	python3 -m pip install .

build:
	make clean
	python3 -m build

upload-test:
	make build
	python3 -m twine upload --repository testpypi dist/* -u "__token__" -p "${token}"

upload:
	make build
	python3 -m twine upload dist/* -u "__token__" -p "${token}"

docs:
	# docs-init must have been run once
	make docs-generate
	source env/bin/activate && cd docs && make html

docs-init:
	mkdir -p docs
	make docs-clean
	cd docs && yes y | make sphinx-quickstart
	make docs

docs-clean:
	rm -rf docs/source/modules
	rm -rf docs/build

docs-show:
	open docs/build/html/index.html

docs-watch: 
	# init docs
	make docs-show
	# open window
	make docs-show
	# watch for any changes & update accordingly
	find docs/source -type f -name '*.rst' -o -name '*.md' -o -name '*.css' -prune -o -name 'docs/source/modules/*.rst' | entr make docs

docs-generate:
	make docs-clean
	# generate modules from python source code
	cd docs && sphinx-apidoc -o source/modules ../src/mash
	# generate shell help
	python3 src/examples/shell_example.py -h > ${out}/shell_help.txt
	# generate examples
	echo '# Examples\n' > ${out}/mash_examples.md
	find src/examples/*.py -type f -regex 'src/examples/[a-z][a-z_]*.py' -exec echo '- [{}](${github}{})'  \; >> ${out}/mash_examples.md

tree:
	tree src -L 2 -d
	tree src/mash -L 2 --gitignore -I '_*|*.out'

ast:
	egrep -rh '^class \w+(\(\w+\))?\:' src/mash/shell/ast

web:
	open web/home.html
	python3 src/examples/server.py

