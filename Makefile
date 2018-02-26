install:
	pip3 install -r requirements/prod.txt

install-test: install
	pip3 install -r requirements/dev.txt

install-dev: install-test

test:
	python3 -m unittest test_image_downloader

lint:
	python3 -m pylint image_downloader --disable=redefined-outer-name,no-self-use,too-few-public-methods,line-too-long,unused-argument,invalid-name

lint-strict:
	python3 -m pylint image_downloader
