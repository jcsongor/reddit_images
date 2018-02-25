install:
	pip3 install -r requirements.txt

test:
	python3 -m unittest test_image_downloader

lint:
	python3 -m pylint image_downloader --disable=redefined-outer-name,no-self-use,too-few-public-methods
