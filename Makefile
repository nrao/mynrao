# Gives `make test`, a cleaner clean, & make integration for external tools.

all: build test

develop:
	pip install nose minimock
	python setup.py develop

build:
	python setup.py build

install:
	python setup.py install

test: develop
	python setup.py nosetests

clean:
	python setup.py clean
	rm -fr *.egg-info build
	find . -name '*.pyc' -delete
