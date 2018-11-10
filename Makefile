install:
	pip install -r requirements/prod.txt

install-dev: install
	pip install -r requirements/dev.txt

install-all: install install-dev

test:
	python3 -m unittest test_image_downloader

lint:
	python3 -m pylint image_downloader --disable=redefined-outer-name,no-self-use,too-few-public-methods,line-too-long,unused-argument,invalid-name

lint-strict:
	python3 -m pylint image_downloader

push:
	make test && make lint && git push
