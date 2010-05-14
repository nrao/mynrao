# Gives `make test`, a cleaner clean, & make integration for external tools.

all: build test

build:
	python setup.py build

install:
	python setup.py install

test:
	python setup.py nosetests

clean:
	python setup.py clean
	rm -fr *.egg-info build
	find . -name '*.pyc' -delete
