
[![Build Status](https://travis-ci.org/jcsongor/reddit_bots.svg?branch=master)](https://travis-ci.org/jcsongor/reddit_bots)

# reddit_bots
Collection of reddit bots

##image_downloader.py
Bot that downloads images from top reddit posts

###Usage example:
Fetch 5 pictures from [/r/FractalPorn](https://reddit.com/r/FractalPorn) and [/r/ExposurePorn](https://reddit.com/r/ExposurePorn) from hot posts and dowload it to `~/backgrounds`

```shell
    $ python3 image_downloader.py FractalPorn,ExposurePorn 5 ~/backgrounds
```
