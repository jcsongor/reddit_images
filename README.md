
[![Build Status](https://travis-ci.org/jcsongor/reddit_images.svg?branch=master)](https://travis-ci.org/jcsongor/reddit_images)

## Image downloader
Bot that downloads images from top reddit posts

### Example usage:
Fetch 5 pictures from [/r/FractalPorn](https://reddit.com/r/FractalPorn) and [/r/ExposurePorn](https://reddit.com/r/ExposurePorn) from hot posts and dowload it to `~/backgrounds`

```shell
    $ python3 image_downloader.py --subreddits=FractalPorn,ExposurePorn --count=5 --to=/usr/share/images/desktop-base --botname=backgrounddownloader --orientation=landscape
```
