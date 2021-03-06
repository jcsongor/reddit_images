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
        self._settings = Settings()
        self.allowed_types = self._settings['filetypes']

    def is_image(self, file):
        """Check file contents to see if it looks like an image"""
        return what(file) in self.allowed_types

    def is_orientation_ok(self, file):
        """Check image orientation according to settings"""
        size = Image.open(file).size
        orientation = self._settings['orientation']
        if self._is_square(*size) or orientation == 'both':
            return True
        return self._get_orientation(*size) == orientation

    def is_landscape_image(self, file):
        """Check image size to determine if it is landscape or portrait"""
        size = Image.open(file).size
        return self._get_orientation(*size) == 'landscape'

    def _get_orientation(self, width, height):
        return 'portrait' if width < height else 'landscape'

    def _is_square(self, width, height):
        return width == height


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
    __shared_dict = {}
    _default_settings = {
        'subreddits': None,
        'count': 1,
        'to': '.',
        'botname': '.',
        'filetypes': 'jpeg, png',
        'orientation': 'both',
    }
    _settings = None
    _ORIENTATIONS = ['portrait', 'landscape', 'both']

    def __init__(self, *_, **kwargs):
        self.__dict__ = self.__shared_dict
        if self._settings is None:
            self._settings = self._get_settings(kwargs)
            self._validate_settings()

    def __getitem__(self, key):
        if not self._valid_setting(key):
            raise KeyError(key)
        return self._settings[key]

    def _get_settings(self, kwargs):
        settings = self._read_settings(kwargs)
        return self._parse_settings(settings)

    def _validate_settings(self):
        if self._settings['orientation'] not in self._ORIENTATIONS:
            raise ValueError(
                'Orientation should be one of the following: %s' %
                ', '.join(self._ORIENTATIONS)
            )

    def _valid_setting(self, setting):
        return setting in self._default_settings

    def _read_settings(self, kwargs):
        cli_arguments = self._get_cli_arguments()
        return ChainMap(kwargs, cli_arguments, os.environ, self._default_settings)

    def _parse_settings(self, settings):
        settings['subreddits'] = self._csv_to_dict(settings['subreddits'])
        settings['filetypes'] = self._csv_to_dict(settings['filetypes'])
        settings['count'] = int(settings['count'])
        return settings

    def _get_cli_arguments(self):
        parser = ArgumentParser()
        parser.add_argument('-s', '--subreddits')
        parser.add_argument('-c', '--count')
        parser.add_argument('-t', '--to')
        parser.add_argument('-f', '--filetypes')
        parser.add_argument('-b', '--botname')
        parser.add_argument('-o', '--orientation')
        return {k: v for k, v in vars(parser.parse_args()).items() if v}

    def _csv_to_dict(self, csv):
        return (subreddit.strip() for subreddit in csv.split(','))



if __name__ == "__main__":
    settings = Settings()
    image_downloader = ImageDownloader(settings['botname'])
    count = int(settings['count'])
    for subreddit_name in settings['subreddits']:
        image_downloader.download_images_from_subreddit(subreddit_name, count, settings['to'])
