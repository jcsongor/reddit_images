
[![Build Status](https://travis-ci.org/jcsongor/reddit_bots.svg?branch=master)](https://travis-ci.org/jcsongor/reddit_bots)

# Reddit bots
Collection of reddit bots

## Image downloader
Bot that downloads images from top reddit posts

### Usage example:
Fetch 5 pictures from [/r/FractalPorn](https://reddit.com/r/FractalPorn) and [/r/ExposurePorn](https://reddit.com/r/ExposurePorn) from hot posts and dowload it to `~/backgrounds`

```shell
    $ python3 image_downloader.py --subreddits=FractalPorn,ExposurePorn --count=5 --to=/usr/share/images/desktop-base --botname=backgrounddownloader
```
