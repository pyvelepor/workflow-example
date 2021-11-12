import scrapy
import pathlib

class Replays(scrapy.Spider):
    name = "replays"

    def __init__(self, *args, debug=None, format="gen8ou", feed_base_dir=".", max_replays=10, **kwargs):
        super().__init__(*args, **kwargs)
        self.__page_number = 1
        self.__start_url = "https://replay.pokemonshowdown.com/search/?output=html&format={format}&page={page_number}"
        self.format = format
        self.feed_base_dir = pathlib.Path(feed_base_dir)
        self.max_replays = max_replays

        if debug is not None:
            self.__start_url = pathlib.Path(debug).resolve().as_uri()

    def start_requests(self):
        yield self.replay_listing_request(page_number=0,
                                          format=self.format,
                                          callback=self.parse_replay_listing,
                                          num_scraped=0)

    def parse_replay(self, response):
        yield response.json()

    def replay_listing_request(self, page_number, format, callback, num_scraped=0):
        start_url = self.__start_url.format(format=format, page_number=page_number)
        return scrapy.Request(url=start_url,
                              callback=callback,
                              cb_kwargs={
                                  "page_number": page_number,
                                  "num_scraped": num_scraped
                              })


    def replay_urls(self, response):
        for html_tag in response.xpath("//h3 | //a"):
            if html_tag.root.tag == "h3":
                continue

            elif html_tag.root.tag != "a":
                continue

            elif "?" in html_tag.attrib["href"]:
                continue

            href = html_tag.attrib["href"]

            yield f"https://replay.pokemonshowdown.com{href}.json"

    def parse_replay_listing(self, response, page_number=0, num_scraped=0):
        for index, replay_url in enumerate(self.replay_urls(response), start=num_scraped):
            if index == self.max_replays:
                break

            yield scrapy.Request(url=replay_url, callback=self.parse_replay)

        if index < num_scraped:
            yield self.replay_listing_request(page_number=page_number+1,
                                              format=self.format,
                                              callback=self.parse_replay_listing,
                                              num_scraped=index + 1)