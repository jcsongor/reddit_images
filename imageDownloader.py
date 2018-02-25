#!/usr/bin/python
import praw
import sys
import validators
from imghdr import what
from os import remove, rename
from urllib.request import urlretrieve
from uuid import uuid4
from PIL import Image


class ImageDownloader(object):
    """Class to download top `n` images from a given subreddit"""

    def download_images_from_subreddit(self, bot_name, subreddit_name, number_of_images, target_directory):
        url_provider = UrlProvider(bot_name)
        image_fetcher = ImageFetcher()
        for url in url_provider.get_urls(subreddit_name, number_of_images):
            image_fetcher.fetch(url, target_directory, subreddit_name)


class ImageFetcher(object):
    """Class to validate and download an image"""
    _TMP_PATH = '/tmp/'

    def fetch(self, url, target_dir, subreddit_name):
        url_validator = UrlValidator()
        temp_file = self._TMP_PATH + str(uuid4())
        if url_validator.is_image(url):
            urlretrieve(url, temp_file)
            target_file = self._generate_filename(subreddit_name, target_dir, url)
            self._move_from_temp_if_is_image(temp_file, target_file)

    def _generate_filename(self, subreddit_name, target_dir, url):
        return target_dir.rstrip('/') + '/' + subreddit_name + '_' + url.split('/')[-1].lstrip('.')

    def _move_from_temp_if_is_image(self, temp_file, target_file):
        if FileValidator().is_image(temp_file):
            rename(temp_file, target_file)
        else:
            remove(temp_file)


class FileValidator(object):
    _ALLOWED_TYPES = ['jpeg', 'png']

    def is_image(self, file):
        return what(file) in self._ALLOWED_TYPES

    def is_landscape_image(self, file):
        size = Image.open(file).size
        return size[0] > size[1]


class UrlProvider(object):
    """Class to get a list of image urls from hot posts"""

    def __init__(self, bot_name):
        self.reddit = praw.Reddit(bot_name)

    def get_urls(self, subreddit_name, number_of_images):
        subreddit = self.reddit.subreddit(subreddit_name)
        return [submission.url for submission in subreddit.hot(limit=number_of_images)]


class UrlValidator(object):
    """Class to validate urls"""
    _image_extensions = [
        'jpg',
        'ai',
        'rgb',
        'gif',
        'pbm',
        'pgm',
        'ppm',
        'tiff',
        'rast',
        'xbm',
        'jpeg',
        'bmp',
        'png',
        'webp',
        'exr',
    ]

    def is_image(self, url):
        return self.is_valid(url) and url.count('.') and url.split('.')[-1] in self._image_extensions

    def is_valid(self, url):
        return validators.url(url) is True


if __name__ == "__main__":
    image_downloader = ImageDownloader()
    for subreddit in sys.argv[1].split(','):
        image_downloader.download_images_from_subreddit('bgr', subreddit, int(sys.argv[2]), sys.argv[3] + '/')
