from collections import namedtuple
from unittest import TestCase
from unittest.mock import MagicMock, patch, call

from unittest_data_provider import data_provider

from image_downloader import *


class ImageDownloaderTest(TestCase):
    _bot_name = 'bot_name'
    _subreddit_name = 'subreddit_name'
    _target_directory = 'target_directory'
    _number_of_images = 100

    def setUp(self):
        self._patch_urlprovider()
        self.image_downloader = ImageDownloader(self._bot_name)

    def test_init_creates_urlprovider_with_correct_bot_name(self):
        self._urlprovider.assert_called_with(self._bot_name)

    def test_download_images_from_subreddit_calls_urlprovider_with_correct_parameters(self):
        self._download_images()

        self._urlprovider.return_value.get_urls.assert_called_with(self._subreddit_name, self._number_of_images)

    @patch('image_downloader.ImageFetcher.fetch')
    def test_download_images_from_subreddit_calls_fetch_for_each_url(self, fetch):
        image_urls = ['img1', 'img2']
        self._urlprovider.return_value.get_urls.return_value = image_urls

        self._download_images()

        fetch.assert_has_calls([call(url, self._target_directory, self._subreddit_name) for url in image_urls])

    def _patch_urlprovider(self):
        patcher = patch('image_downloader.UrlProvider')
        self._urlprovider = patcher.start()
        self.addCleanup(patcher.stop)

    def _download_images(self):
        self.image_downloader.download_images_from_subreddit(
            self._subreddit_name,
            self._number_of_images,
            self._target_directory
        )


@patch('os.rename')
@patch('image_downloader.urlretrieve')
class ImageFetcherTest(TestCase):
    _image_filename = 'image.jpeg'
    _image_url = 'http://example.org/' + '.' + _image_filename
    _target_directory = 'target_directory'
    _uuid_value = 'uuid'
    _subreddit_name = 'subreddit_name'

    def setUp(self):
        self._url_validator = self._patch('image_downloader.UrlValidator')
        self._file_validator = self._patch('image_downloader.FileValidator')
        self._patch('image_downloader.uuid4').return_value = self._uuid_value
        self._image_fetcher = ImageFetcher()

    @patch('image_downloader.what')
    def test_fetch_image_downloads_image_to_tmp_file(self, what, urlretrieve, _):
        self._url_validator.is_image.return_value = True
        self._file_validator.is_image.return_value = True
        what.return_value = 'jpeg'

        self._image_fetcher.fetch(self._image_url, self._target_directory, self._subreddit_name)

        urlretrieve.assert_called_with(self._image_url, self._get_tmp_file_path())

    def test_fetch_image_does_not_download_image_if_url_is_not_an_image_url(self, urlretrieve, _):
        self._url_validator.return_value.is_image.return_value = False

        self._image_fetcher.fetch(self._image_url, self._target_directory, self._subreddit_name)

        urlretrieve.assert_not_called()

    def test_fetch_image_moves_file_to_target_directory_if_it_is_an_image(self, _, rename):
        self._url_validator.return_value.is_image.return_value = True
        self._file_validator.return_value.is_image.return_value = True

        self._image_fetcher.fetch(self._image_url, self._target_directory, self._subreddit_name)

        target_filename = self._target_directory + '/' + self._subreddit_name + '_' + self._image_filename
        rename.assert_called_with(self._get_tmp_file_path(), target_filename)

    @patch('os.remove')
    def test_fetch_image_removes_file_if_it_is_not_an_image(self, remove, _, rename):
        self._url_validator.return_value.is_image.return_value = True
        self._file_validator.return_value.is_image.return_value = False

        self._image_fetcher.fetch(self._image_url, self._target_directory, self._subreddit_name)

        rename.assert_not_called()
        remove.assert_called_with(self._get_tmp_file_path())

    def _get_tmp_file_path(self):
        return self._image_fetcher._TMP_PATH + self._uuid_value

    def _patch(self, target):
        patcher = patch(target)
        patched = patcher.start()
        self.addCleanup(patcher.stop)
        return patched


class FileValidatorTest(TestCase):
    _filename = 'filename'
    _settings = {'filetypes': ['jpeg', 'png']}

    def setUp(self):
        self._patch_settings()
        self._file_validator = FileValidator()

    @patch('image_downloader.what')
    def test_is_image_returns_true_if_file_is_an_image(self, what):
        what.return_value = 'jpeg'

        is_image_result = self._file_validator.is_image(self._filename)

        self.assertTrue(is_image_result)

    @patch('image_downloader.what')
    def test_is_image_returns_false_if_file_is_not_an_image(self, what):
        what.return_value = 'exe'

        is_image_result = self._file_validator.is_image(self._filename)

        self.assertFalse(is_image_result)

    orientations = lambda: (
            ('landscape', (1280, 720), True),
            ('landscape', (720, 1280), False),
            ('portrait', (1280, 720), False),
            ('portrait', (720, 1280), True),
            ('both', (1280, 720), True),
            ('both', (720, 1280), True),
        )

    @data_provider(orientations)
    @patch('image_downloader.Image.open')
    def test_is_orientation_ok(self, orientation, dimensions, expected_result, image_open):
        self._settings['orientation'] = orientation
        image_open.return_value.size = dimensions

        actual = self._file_validator.is_orientation_ok(self._filename)

        self.assertEqual(actual, expected_result)

    @patch('image_downloader.Image.open')
    def test_is_landscape_image_returns_true_for_landscape_images(self, image_open):
        image_open.return_value.size = (1280, 720)

        landscape_result = self._file_validator.is_landscape_image(self._filename)

        self.assertTrue(landscape_result)

    @patch('image_downloader.Image.open')
    def test_is_landscape_image_returns_false_for_portrait_images(self, image_open):
        image_open.return_value.size = (720, 1280)

        landscape_result = self._file_validator.is_landscape_image(self._filename)

        self.assertFalse(landscape_result)

    def _patch_settings(self):
        patcher = patch('image_downloader.Settings')
        settings = patcher.start()
        self.addCleanup(settings.stop)
        settings.return_value.__getitem__ = lambda _, key: self._settings[key]


class UrlProviderTest(TestCase):
    _subreddit_name = 'subreddit_name'
    _number_of_images = 100

    def setUp(self):
        self._subreddit = MagicMock()
        self._patch_reddit()
        self._url_provider = UrlProvider('bot_name')

    def test_get_urls_fetches_given_subreddit(self):
        self._url_provider.get_urls(self._subreddit_name, self._number_of_images)

        self._subreddit.assert_called_once_with(self._subreddit_name)

    def test_get_urls_fetches_given_number_of_hot_submissions(self):
        self._url_provider.get_urls(self._subreddit_name, self._number_of_images)

        self._subreddit.return_value.hot.assert_called_once_with(limit=self._number_of_images)

    def test_get_urls_extracts_urls_from_submissions(self):
        expected_urls = ['https://example.org/dummy.jpeg'] * self._number_of_images
        self._subreddit.return_value.hot.return_value = [MagicMock(url=url) for url in expected_urls]

        result_urls = list(self._url_provider.get_urls(self._subreddit_name, self._number_of_images))

        self.assertEqual(result_urls, expected_urls)

    def _patch_reddit(self):
        patcher = patch('praw.Reddit')
        reddit = patcher.start()
        self.addCleanup(reddit.stop())

        reddit.return_value.subreddit = self._subreddit


class UrlValidatorTest(TestCase):
    def setUp(self):
        self._url_validator = UrlValidator()

    def test_is_valid_returns_true_for_valid_url(self):
        self.assertTrue(self._url_validator.is_valid('http://example.org/test/test.jpeg'))

    def test_is_valid_returns_false_for_invalid_url(self):
        self.assertFalse(self._url_validator.is_valid('invalid'))

    def test_is_image_returns_true_for_image_urls(self):
        self.assertTrue(self._url_validator.is_image('http://example.org/test/test.jpeg'))

    def test_is_image_returns_false_for_non_image_urls(self):
        self.assertFalse(self._url_validator.is_image('http://example.org/test/test.exe'))

    def test_is_image_returns_false_for_urls_with_no_extension(self):
        self.assertFalse(self._url_validator.is_image('http://example.org/test/test'))

    def test_is_image_returns_false_for_invalid_url(self):
        self.assertFalse(self._url_validator.is_image('valami.jpeg'))
