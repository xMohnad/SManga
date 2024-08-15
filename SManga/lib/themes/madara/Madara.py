import base64
import json
import re
import scrapy
from scrapy.http import Response
from scrapy.selector import Selector

from SManga.items import ChapterItem
from SManga.lib.cryptoaes import CryptoAES

# response.css("head > meta[property^='og:image']").xpath("@content") > cover
# response.css(".c-breadcrumb li:nth-child(3) > a::text").get().strip() > name
# response.css(".c-breadcrumb .active::text").get().strip() > title
# response.css("#manga-reading-nav-foot .select-pagination .nav-next > a::attr(href)").get() > next
# chapter_img_selector = "div.page-break, li.blocks-gallery-item, .reading-content .text-left:not(:has(.blocks-gallery-item)) img"


class Madara(scrapy.Spider):
    name = ""
    allowed_domains = []
    base_url = ""

    next_selector = ".select-pagination .nav-next a:not(.back)::attr(href)"
    home_selector = "#chapter-heading > a.back::attr(href)"

    manganame = None
    cover = None
    scraped_home = False

    def start_requests(self):
        yield scrapy.Request(self.url, dont_filter=True)

    title_selector = ".c-breadcrumb .active::text"

    def parse(self, response: Response):
        if not self.scraped_home:
            self.scraped_home = True
            self.get_info(response)
            if not self.manganame or not self.cover:
                home_url = response.css(self.home_selector).get()
                if home_url:
                    yield scrapy.Request(
                        url=home_url,
                        callback=self.get_info_and_retry,
                        meta={"retry": response.url},
                        dont_filter=True,
                    )
                    return

        item = ChapterItem()

        item["manganame"] = self.manganame
        item["cover"] = self.cover
        item["title"] = response.css(self.title_selector).get().strip()
        item["images"] = self.parse_chapter_image(response)
        item["document_location"] = response.url

        yield item
        next_page_url = response.css(self.next_selector).get()
        if next_page_url:
            yield response.follow(url=next_page_url.strip(), callback=self.parse)

    chapter_selector = "div.page-break img, li.blocks-gallery-item img, .reading-content .text-left:not(:has(.blocks-gallery-item)) img"
    chapter_protector_selector = "#chapter-protector-data"

    def parse_chapter_image(self, response: Response):
        image = response.css(self.chapter_selector)
        if image:
            return [self.image_from_element(img).strip() for img in image]
        return self.parse_protector_image(response)

    def parse_protector_image(self, response: Response) -> list:
        chapter_protector = response.css(self.chapter_protector_selector).get()
        if not chapter_protector:
            return []

        password = re.search(
            r"wpmangaprotectornonce='(.*?)';", chapter_protector
        ).group(1)
        chapter_data_str = (
            re.search(r"chapter_data='(.*?)';", chapter_protector)
            .group(1)
            .replace("\\/", "/")
        )
        chapter_data = json.loads(chapter_data_str)

        salted = b"Salted__"
        salt = bytes.fromhex(chapter_data["s"])
        unsalted_ciphertext = base64.b64decode(chapter_data["ct"])

        ciphertext = salted + salt + unsalted_ciphertext
        decrypted_text = CryptoAES.decrypt(base64.b64encode(ciphertext), password)

        img_list_string = json.loads(decrypted_text.encode("utf-8"))
        return json.loads(img_list_string)

    manganame_xpath = '//li[@class="active"]/preceding-sibling::li[1]/a/text()'
    cover_selector = "head > meta[property^='og:image']::attr(content)"

    def get_info(self, response: Response):
        manganame = response.xpath(self.manganame_xpath).get()
        if manganame:
            self.manganame = manganame.strip()
        self.cover = response.css(self.cover_selector).get()

    home_manganame_selector = ".tab-summary .post-title > h1::text"
    home_cover_selector = ".tab-summary .summary_image > a > img"

    def get_info_and_retry(self, response: Response):
        self.manganame = response.css(self.home_manganame_selector).get().strip()
        self.cover = self.image_from_element(response.css(self.home_cover_selector))
        retry_url = response.meta.get("retry")
        if retry_url:
            yield scrapy.Request(url=retry_url, callback=self.parse, dont_filter=True)

    @staticmethod
    def image_from_element(element: Selector) -> str:
        for attr in ["data-lazy-src", "data-src", "srcset", "data-cfsrc", "src"]:
            if element.attrib.get(attr):
                if "srcset" in attr:
                    return element.attrib["srcset"].split(" ")[0]
                return element.attrib.get(attr)
        return ""
