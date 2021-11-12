import pathlib

def uri_params(params, spider):
    base_feed_dir = spider.feed_base_dir.resolve().as_uri()
    format = spider.format

    return {
        **params,
        "format": format,
        "base_feed_dir": base_feed_dir
    }