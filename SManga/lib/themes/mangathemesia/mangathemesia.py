import scrapy
from SManga.items import ChapterItem
from scrapy.http import Response
from scrapy.selector import Selector
import json
import base64

# script_base64_selector ="script[src^='data:text/javascript;base64,dHNfcmVhZGVyLnJ1bih7']"


class MangaThemesiaSpider(scrapy.Spider):
    name = ""
    allowed_domains = []
    base_url = ""

    cover_selector = ".infomanga > div[itemprop=image] img, .thumb img"
    manganame_selector = "div.infox > h1::text"
    title_selector = "div.headpost > h1::text"
    script_xpath = "//script[contains(text(),'ts_reader')]//text()"

    #  "ts_reader.run({" in base64
    script_base64_xpath = '//script[starts-with(@src, "data:text/javascript;base64,dHNfcmVhZGVyLnJ1bih7")]'

    manganame = None
    cover = None

    def start_requests(self):
        yield scrapy.Request(self.url, dont_filter=True)

    def parse(self, response: Response):
        if not self.manganame or not self.cover:
            home_url = response.css("div.headpost > div > a::attr(href)").get()
            if home_url:
                yield scrapy.Request(
                    url=home_url,
                    callback=self.get_info_and_retry,
                    meta={"retry": response.url},
                    dont_filter=True,
                )
                return

        item, next_url = self.extract_data(response)

        yield item

        if next_url:
            yield scrapy.Request(url=next_url, callback=self.parse)

    def extract_data(self, response: Response):
        script_con = (
            response.xpath(self.script_xpath).get()
            or response.xpath(self.script_base64_xpath).get()
        )
        if not script_con:
            return None, None

        ts_reader = self.parse_script_content(script_con)
        sources = ts_reader.get("sources", [])

        item = ChapterItem()

        item["manganame"] = self.manganame
        item["cover"] = self.cover
        item["title"] = response.css(self.title_selector).get()
        item["images"] = sources[0].get("images", [])
        item["document_location"] = response.url

        return item, ts_reader.get("nextUrl")

    def get_info_and_retry(self, response: Response):
        self.manganame = response.css(self.manganame_selector).get()
        self.cover = self.img_attr(response.css(self.cover_selector))
        retry_url = response.meta.get("retry")
        if retry_url:
            yield response.follow(url=retry_url, callback=self.parse, dont_filter=True)

    def img_attr(self, element: Selector):
        for attr in ["data-lazy-src", "data-src", "data-cfsrc", "src"]:
            if element.attrib.get(attr):
                return element.attrib.get(attr)
        return None

    def parse_script_content(self, script_content):
        if "base64," in script_content:
            script_content = self.base64_to_str(script_content)
        json_string = script_content.split("ts_reader.run(", 1)[1].split(");", 1)[0]
        return json.loads(json_string)

    def base64_to_str(self, script):
        base64_data = script.split("base64,")[1].split('"></script>')[0]
        return base64.b64decode(base64_data).decode("utf-8")
