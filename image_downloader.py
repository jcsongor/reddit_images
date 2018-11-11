#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Download images from top reddit posts

Example:
    Fetch 5 pictures from /r/FractalPorn and /r/ExposurePorn from hot posts and
    download it to ~/backgrounds
    $ python image_downloader.py --subreddits=FractalPorn,ExposurePorn --count=5 --to=~/backgrounds

Todo:
    * optionally download from hot/top etc
    * check if file exists, add option to overwrite/skip

"""
from argparse import ArgumentParser
from collections import ChainMap
from imghdr import what
from urllib.request import urlretrieve
import os
from uuid import uuid4
from PIL import Image
import praw
import validators


class ImageDownloader:
    """Download top images from a given reddit"""
    def __init__(self, bot_name):
        self._url_provider = UrlProvider(bot_name)
        self._image_fetcher = ImageFetcher()

    def download_images_from_subreddit(self, subreddit_name, number_of_images, target_directory):
        """Download top `n` images from a given subreddit"""
        for url in self._url_provider.get_urls(subreddit_name, number_of_images):
            self._image_fetcher.fetch(url, target_directory, subreddit_name)


class ImageFetcher:
    """Validate and download an image"""
    _TMP_PATH = '/tmp/'
    def __init__(self):
        self._url_validator = UrlValidator()
        self._file_validator = FileValidator()

    def fetch(self, url, target_dir, subreddit_name):
        """Download one url, check if it is an image. If it isn't delete it."""
        temp_file = self._TMP_PATH + str(uuid4())
        if self._url_validator.is_image(url):
            urlretrieve(url, temp_file)
            target_file = self._generate_filename(subreddit_name, target_dir, url)
            self._move_from_temp_if_is_image(temp_file, target_file)

    def _generate_filename(self, subreddit, target_dir, url):
        return target_dir.rstrip('/') + '/' + subreddit + '_' + url.split('/')[-1].lstrip('.')

    def _move_from_temp_if_is_image(self, temp_file, target_file):
        if self._file_validator.is_image(temp_file):
            os.rename(temp_file, target_file)
        else:
            os.remove(temp_file)


class FileValidator:
    """Validate file type and image format"""
    def __init__(self):
        self.allowed_types = Settings()['filetypes']

    def is_image(self, file):
        """Check file contents to see if it looks like an image"""
        return what(file) in self.allowed_types

    def is_orientation_ok(self, file):
        """Check image orientation according to settings"""
        size = Image.open(file).size
        orientation = Settings()['orientation']
        if size[0] == size[1] or orientation == 'both':
            return True
        if size[0] > size[1]:
            return orientation == 'landscape'
        return orientation == 'portrait'

    def is_landscape_image(self, file):
        """Check image size to determine if it is landscape or portrait"""
        size = Image.open(file).size
        return size[0] > size[1]


class UrlProvider:
    """Class to get a list of image urls from hot posts"""

    def __init__(self, bot_name):
        self.reddit = praw.Reddit(bot_name)

    def get_urls(self, subreddit_name, number_of_images):
        """Get urls for given number of hot posts from given subreddit"""
        subreddit = self.reddit.subreddit(subreddit_name)
        return (submission.url for submission in subreddit.hot(limit=number_of_images))


class UrlValidator:
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


class Settings:
    """Handle settings from env and cli params"""
    _settings = {
        'subreddits': None,
        'count': 1,
        'to': '.',
        'botname': '.',
        'filetypes': 'jpeg, png',
        'orientation': 'both',
    }
    _ORIENTATIONS = ['portrait', 'landscape', 'both']

    def __getitem__(self, key):
        return self._settings[key]

    def __init__(self, *_, **kwargs):
        parser = ArgumentParser()
        parser.add_argument('-s', '--subreddits')
        parser.add_argument('-c', '--count')
        parser.add_argument('-t', '--to')
        parser.add_argument('-f', '--filetypes')
        parser.add_argument('-b', '--botname')
        parser.add_argument('-o', '--orientation')

        cli_arguments = {k: v for k, v in vars(parser.parse_args()).items() if v}
        self._settings = ChainMap(kwargs, cli_arguments, os.environ, self._settings)

        self._settings['subreddits'] = self._csv_to_dict(self._settings['subreddits'])
        self._settings['filetypes'] = self._csv_to_dict(self._settings['filetypes'])
        self._settings['count'] = int(self._settings['count'])
        self._validate_orientation()

    def _csv_to_dict(self, csv):
        return (subreddit.strip() for subreddit in csv.split(','))

    def _validate_orientation(self):
        if self._settings['orientation'] not in self._ORIENTATIONS:
            raise ValueError(
                'Orientation should be one of the following: %s' %
                ', '.join(self._ORIENTATIONS)
            )



if __name__ == "__main__":
    settings = Settings()
    image_downloader = ImageDownloader(settings['botname'])
    count = int(settings['count'])
    for subreddit_name in settings['subreddits']:
        image_downloader.download_images_from_subreddit(subreddit_name, count, settings['to'])
