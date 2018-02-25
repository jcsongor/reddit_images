from unittest import TestCase
from unittest.mock import MagicMock, patch, call

from imageDownloader import *


class ImageDownloaderTest(TestCase):
    _bot_name = 'bot_name'
    _subreddit_name = 'subreddit_name'
    _target_directory = 'target_directory'

    def setUp(self):
        self.image_downloader = ImageDownloader()

    @patch('imageDownloader.UrlProvider')
    def test_download_images_from_creates_urlprovider_with_correct_bot_name(self, url_provider):
        self.image_downloader.download_images_from_subreddit(self._bot_name,
                                                             self._subreddit_name, 100,
                                                             self._target_directory)
        url_provider.assert_called_with(self._bot_name)

    @patch('imageDownloader.UrlProvider')
    def test_download_images_from_subreddit_calls_urlprovider_with_correct_parameters(self, url_provider):
        self.image_downloader.download_images_from_subreddit(self._bot_name,
                                                             self._subreddit_name,
                                                             100,
                                                             self._target_directory)
        url_provider.return_value.get_urls.assert_called_with(self._subreddit_name, 100)

    @patch('imageDownloader.ImageFetcher.fetch')
    @patch('imageDownloader.UrlProvider')
    def test_download_images_from_subreddit_calls_fetch_for_each_url(self, url_provider, fetch):
        image_urls = ['img1', 'img2']
        url_provider.return_value.get_urls.return_value = image_urls
        self.image_downloader.download_images_from_subreddit(self._bot_name,
                                                             self._subreddit_name, 100,
                                                             self._target_directory)
        fetch.assert_has_calls([call(url, self._target_directory, self._subreddit_name) for url in image_urls])


class ImageFetcherTest(TestCase):
    _image_filename = 'image.jpeg'
    _image_url = 'http://example.org/' + '.' + _image_filename
    _target_directory = 'target_directory'
    _uuid_value = 'uuid'
    _subreddit_name = 'subreddit_name'

    def setUp(self):
        self._image_fetcher = ImageFetcher()

    @patch('imageDownloader.rename')
    @patch('imageDownloader.what')
    @patch('imageDownloader.UrlValidator')
    @patch('imageDownloader.urlretrieve')
    def test_fetch_image_downloads_image_to_tmp_file(self, urlretrieve, urlvalidator, what, rename):
        urlvalidator.return_value.is_valid.return_value = True
        urlvalidator.return_value.is_image.return_value = True
        what.return_value = 'jpeg'
        self._fetch_image()
        urlretrieve.assert_called_with(self._image_url, self._get_tmp_file_path())

    @patch('imageDownloader.rename')
    @patch('imageDownloader.UrlValidator')
    @patch('imageDownloader.urlretrieve')
    def test_fetch_image_does_not_download_image_if_url_is_not_valid(self, urlretrieve, urlvalidator, rename):
        urlvalidator.return_value.is_valid.return_value = False
        urlvalidator.return_value.is_image.return_value = True
        self._fetch_image()
        urlretrieve.assert_not_called()

    @patch('imageDownloader.rename')
    @patch('imageDownloader.UrlValidator')
    @patch('imageDownloader.urlretrieve')
    def test_fetch_image_does_not_download_image_if_url_is_not_a_valid_image_url(self,
                                                                                 urlretrieve,
                                                                                 urlvalidator,
                                                                                 rename):
        urlvalidator.return_value.is_valid.return_value = True
        urlvalidator.return_value.is_image.return_value = False
        self._fetch_image()
        urlretrieve.assert_not_called()

    @patch('imageDownloader.rename')
    @patch('imageDownloader.FileValidator')
    @patch('imageDownloader.UrlValidator')
    @patch('imageDownloader.urlretrieve')
    def test_fetch_image_moves_file_to_target_directory_if_it_is_of_allowed_type(self,
                                                                                 urlretrieve,
                                                                                 urlvalidator,
                                                                                 filevalidator,
                                                                                 rename):
        urlvalidator.return_value.is_valid.return_value = True
        urlvalidator.return_value.is_image.return_value = True
        filevalidator.return_value.is_image.return_value = True
        self._fetch_image()
        target_filename = self._target_directory + '/' + self._subreddit_name + '_' + self._image_filename
        rename.assert_called_with(self._get_tmp_file_path(), target_filename)

    @patch('imageDownloader.remove')
    @patch('imageDownloader.rename')
    @patch('imageDownloader.FileValidator')
    @patch('imageDownloader.UrlValidator')
    @patch('imageDownloader.urlretrieve')
    def test_fetch_image_removes_file_if_it_is_not_an_image(self, urlretrieve, urlvalidator, filevalidator, rename, remove):
        urlvalidator.return_value.is_valid.return_value = True
        urlvalidator.return_value.is_image.return_value = True
        filevalidator.return_value.is_image.return_value = False
        self._fetch_image()
        rename.assert_not_called()
        remove.assert_called_with(self._get_tmp_file_path())

    @patch('imageDownloader.uuid4')
    def _fetch_image(self, uuid):
        uuid.return_value = self._uuid_value
        self._image_fetcher.fetch(self._image_url, self._target_directory, self._subreddit_name)

    def _get_tmp_file_path(self):
        return self._image_fetcher._TMP_PATH + self._uuid_value

class FileValidatorTest(TestCase):
    def setUp(self):
        self._file_validator = FileValidator()

    @patch('imageDownloader.what')
    def test_is_image_returns_true_if_file_is_an_image(self, what):
        what.return_value = 'jpeg'
        self.assertTrue(self._file_validator.is_image('filename'))

    @patch('imageDownloader.what')
    def test_is_image_returns_false_if_file_is_not_an_image(self, what):
        what.return_value = 'exe'
        self.assertFalse(self._file_validator.is_image('filename'))


class UrlProviderTest(TestCase):
    _subreddit_name = 'subreddit_name'
    _number_of_images = 100

    @patch('praw.Reddit')
    def setUp(self, reddit):
        self.subreddit = MagicMock()
        reddit.return_value = MagicMock(subreddit=self.subreddit)
        self.url_provider = UrlProvider('bot_name')

    def test_get_urls_fetches_given_subreddit(self):
        self.url_provider.get_urls(self._subreddit_name, self._number_of_images)
        self.subreddit.assert_called_once_with(self._subreddit_name)

    def test_get_urls_fetches_given_number_of_hot_submissions(self):
        self.url_provider.get_urls(self._subreddit_name, self._number_of_images)
        self.subreddit.return_value.hot.assert_called_once_with(limit=self._number_of_images)

    def test_get_urls_extracts_urls_from_submissions(self):
        expected_urls = ['https://example.org/dummy.jpeg'] * self._number_of_images
        self.subreddit.return_value.hot.return_value = [MagicMock(url=url) for url in expected_urls]

        result_urls = self.url_provider.get_urls(self._subreddit_name, self._number_of_images)

        self.assertEqual(result_urls, expected_urls)


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
        self.assertFalse(self._url_validator.is_image('jpeg'))
