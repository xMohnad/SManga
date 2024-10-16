import json
import base64
from typing import Optional
from scrapy.http import Response
from SManga.lib.themes import BaseSpider


class MangaThemesiaSpider(BaseSpider):
    name = ""
    base_url = ""
    language: str = ""

    extract_details_from_current_page: bool = False

    manganame_selector = "div.infox > h1::text"
    cover_selector = ".infomanga > div[itemprop=image] img, .thumb img"

    title_selector = "div.headpost > h1::text"
    home_page_selector = "div.headpost > div > a::attr(href)"

    script_xpath = "//script[contains(text(),'ts_reader')]//text()"
    script_base64_xpath = '//script[starts-with(@src, "data:text/javascript;base64,dHNfcmVhZGVyLnJ1bih7")]'

    manganame = None
    cover = None

    def extract_title(self, response: Response) -> str:
        title = response.css(self.title_selector).get()
        return title.split("–")[-1].strip() if title else ""

    def extract_home_url(self, response: Response) -> str:
        return response.css(self.home_page_selector).get()

    def extract_next_page_url(self, response: Response) -> Optional[str]:
        script_content = self.get_script_content(response)
        if not script_content:
            return None
        ts_reader = self.parse_script_content(script_content)
        return ts_reader.get("nextUrl")


    # Extract chapter images

    def parse_chapter_image(self, response: Response) -> list[str]:
        script_content = self.get_script_content(response)
        if not script_content:
            return []
        ts_reader = self.parse_script_content(script_content)
        return self.get_chapter(ts_reader)

    def get_chapter(self, ts_reader: dict):
        return ts_reader.get("sources", [""])[0].get("images", [])

    # Extract manga details

    def extract_manga_name_from_home(self, response: Response) -> str:
        return response.css(self.manganame_selector).get()

    def extract_cover_from_home(self, response: Response) -> str:
        return self.image_from_element(response.css(self.cover_selector))

    # Methods for extracting specific data

    def get_script_content(self, response: Response):
        return (
            response.xpath(self.script_xpath).get()
            or response.xpath(self.script_base64_xpath).get()
        )

    # Method to handle script content parsing
    def parse_script_content(self, script_content):
        if "base64," in script_content:
            script_content = self.base64_to_str(script_content)
        json_string = script_content.split("ts_reader.run(", 1)[1].split(");", 1)[0]
        return json.loads(json_string)

    def base64_to_str(self, script):
        base64_data = script.split("base64,")[1].split('"></script>')[0]
        return base64.b64decode(base64_data).decode("utf-8")
