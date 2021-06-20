test:
	# print difference as a warning
	autopep8 -r --diff .
	flake8 --ignore=E241,E501,W504
	pytest

format:
	autopep8 -r -a -a -a --in-place .

setup:
	pip3 install -r requirements.txt

