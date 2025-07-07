.PHONY: docs web test

github = https://github.com/voschezang/mash/blob/main/
out = docs/source/modules

# auto-generated file
parsetab = src/mash/shell/grammer/parsetab.py

# use .venv if available
PYTHON := $(shell [ -x .venv/bin/python3 ] && echo .venv/bin/python3 || echo python3)
PIP := $(shell [ -x .venv/bin/pip3 ] && echo .venv/bin/pip3 || echo pip3)
VENV := $(shell [ -f .venv/bin/activate ] && echo source .venv/bin/activate || echo true)

test:
	${PYTHON} --version
	# cleanup & remove parsetab
	make clean
	# print difference as a warning
	${PYTHON} -m autopep8 -r --diff src
	#flake8 --ignore=E241,E501,W504 src
	make lint
	(${VENV}; pytest -n 4)

lint:
	# remove auto-generated file
	rm -f ${parsetab}
	# enforce linting
	${PYTHON} -m flake8 src --count --select=E9,F63,F7,F82 --show-source --statistics
	# show lenient errors
	${PYTHON} -m  flake8 src --count --exit-zero --max-complexity=11 --max-line-length=127 --statistics

format:
	${PYTHON} -m autopep8 -r -a -a -a --in-place src/mash)

clean:
	rm -f ${parsetab}
	find . -name '__pycache__' | xargs rm -rf {1}
	#find . -name '__pycache__' -exec rm -rf {} \;
	rm -rf dist
	rm -rf src/*.egg-info
	make docs-clean

install:
	${PIP} install -r requirements.txt
	${PIP} install -r build_requirements.txt

venv:
	python3 -m venv .venv

build:
	make clean
	${PYTHON} -m build

upload-test:
	make build
	${VENV} && twine upload --repository testpypi dist/* -u "__token__" -p "${token}" --verbose

upload:
	make build
	${VENV} && twine upload dist/* -u "__token__" -p "${token}"

docs:
	# docs-init must have been run once
	make docs-generate
	${VENV}; cd docs; make html

docs-init:
	mkdir -p docs
	make docs-clean
	cd docs && yes y | make sphinx-quickstart
	make docs

docs-clean:
	rm -rf ${out}
	rm -rf docs/build

docs-show:
	open docs/build/html/index.html

docs-watch: 
	# init docs
	make docs
	# open window
	make docs-show
	# watch for any changes & update accordingly
	find docs/source -type f -name '*.rst' -o -name '*.md' -o -name '*.css' -prune -o -name 'docs/source/modules/*.rst' | entr make docs

docs-generate:
	make docs-clean
	echo source
	# generate modules from python source code
	${VENV}; cd docs; sphinx-apidoc -o source/modules ../src/mash
	# generate shell help
	${PYTHON} src/examples/shell_example.py -h > ${out}/shell_help.txt
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
	${PYTHON} src/examples/server.py

