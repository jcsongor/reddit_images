#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Download images from top reddit posts

Example:
    Fetch 5 pictures from /r/FractalPorn and /r/ExposurePorn from hot posts and
    dowload it to ~/backgrounds
        $ python3 image_downloader.py --subreddits=FractalPorn,ExposurePorn --count=5 --to=~/backgrounds

Todo:
    * make cli interface more flexible
    * set up default settings
    * make default settings overridable from ENV
    * optionally download only landscape/portrait images
    * optionally download from hot/top etc

"""
import os
from argparse import ArgumentParser
from collections import ChainMap
from imghdr import what
from urllib.request import urlretrieve
from uuid import uuid4

from PIL import Image
import praw
import validators


class ImageDownloader(object):
    """Download top images from a given reddit"""

    def download_images_from_subreddit(self, bot_name,
                                       subreddit_name,
                                       number_of_images,
                                       target_directory):
        """Download top `n` images from a given subreddit"""
        url_provider = UrlProvider(bot_name)
        image_fetcher = ImageFetcher()
        for url in url_provider.get_urls(subreddit_name, number_of_images):
            image_fetcher.fetch(url, target_directory, subreddit_name)


class ImageFetcher(object):
    """Validate and download an image"""
    _TMP_PATH = '/tmp/'

    def fetch(self, url, target_dir, subreddit_name):
        """Download one url, check if it is an image. If it isn't delete it."""
        url_validator = UrlValidator()
        temp_file = self._TMP_PATH + str(uuid4())
        if url_validator.is_image(url):
            urlretrieve(url, temp_file)
            target_file = self._generate_filename(subreddit_name, target_dir, url)
            self._move_from_temp_if_is_image(temp_file, target_file)

    def _generate_filename(self, subreddit, target_dir, url):
        return target_dir.rstrip('/') + '/' + subreddit + '_' + url.split('/')[-1].lstrip('.')

    def _move_from_temp_if_is_image(self, temp_file, target_file):
        if FileValidator().is_image(temp_file):
            os.rename(temp_file, target_file)
        else:
            os.remove(temp_file)


class FileValidator(object):
    """Validate file type and image format"""
    _ALLOWED_TYPES = ['jpeg', 'png']

    def is_image(self, file):
        """Check file contents to see if it looks like an image"""
        return what(file) in self._ALLOWED_TYPES

    def is_landscape_image(self, file):
        """Check image size to determine if it is landscape or portrait"""
        size = Image.open(file).size
        return size[0] > size[1]


class UrlProvider(object):
    """Class to get a list of image urls from hot posts"""

    def __init__(self, bot_name):
        self.reddit = praw.Reddit(bot_name)

    def get_urls(self, subreddit_name, number_of_images):
        """Get urls for given number of hot posts from given subreddit"""
        subreddit = self.reddit.subreddit(subreddit_name)
        return (submission.url for submission in subreddit.hot(limit=number_of_images))


class UrlValidator(object):
    """Class to validate urls"""
    _image_extensions = ['jpg', 'jpeg', 'png']

    def is_image(self, url):
        """Check if url looks like an image - it has proper extension"""
        return self.is_valid(url) and \
               url.count('.') and \
               url.split('.')[-1] in self._image_extensions

    def is_valid(self, url):
        """Check if string looks like a valid url"""
        return validators.url(url) is True


class Settings(object):
    """Handle settings from env and cli params"""
    __settings = None
    default_settings = {
        'subreddits': None,
        'count': 1,
        'to': '.',
    }
    settings = {}

    def __new__(cls, *args, **kwargs):
        if Settings.__settings is None:
            Settings.__settings = object.__new__(cls)
        return Settings.__settings

    def __init__(self, *arg, **kwargs):
        parser = ArgumentParser()
        parser.add_argument('-s', '--subreddits')
        parser.add_argument('-c', '--count')
        parser.add_argument('-t', '--to')

        cli_arguments = {k: v for k, v in vars(parser.parse_args()).items() if v}
        self.settings = ChainMap(kwargs, cli_arguments, os.environ, self.default_settings)



if __name__ == "__main__":
    settings = Settings().settings
    image_downloader = ImageDownloader()
    for subreddit_name in settings['subreddits'].split(','):
        image_downloader.download_images_from_subreddit('bgr', subreddit_name, int(settings['count']), settings['to'])
