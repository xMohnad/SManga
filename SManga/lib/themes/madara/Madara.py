import base64
import json
import re
from scrapy.http import Response
from typing import List, Optional

from SManga.lib.cryptoaes import CryptoAES
from SManga.lib.themes import BaseSpider


class Madara(BaseSpider):
    name = ""
    base_url = ""

    manganame = None
    cover = None
    extract_details_from_script = False

    next_page_selector = ".select-pagination .nav-next a:not(.back)::attr(href)"
    home_selector = "#chapter-heading > a.back::attr(href)"
    title_selector = ".c-breadcrumb .active::text"

    chapter_selector = "div.page-break img, li.blocks-gallery-item img, .reading-content .text-left:not(:has(.blocks-gallery-item)) img"
    chapter_protector_selector = "#chapter-protector-data"

    manganame_xpath = '//li[@class="active"]/preceding-sibling::li[1]/a/text()'
    cover_selector = "head > meta[property^='og:image']::attr(content)"

    home_manganame_selector = ".tab-summary .post-title > h1::text"
    home_cover_selector = ".tab-summary .summary_image > a > img"

    def extract_next_page_url(self, response: Response) -> Optional[str]:
        return response.css(self.next_page_selector).get().strip()

    def extract_home_url(self, response: Response) -> Optional[str]:
        return response.css(self.home_selector).get()

    def extract_title(self, response: Response) -> str:
        return response.css(self.title_selector).get(default="").strip()

    # Extract chapter images

    def parse_chapter_image(self, response: Response) -> List[str]:
        images = self.get_images_from_page(response)
        return images if images else self.parse_protector_image(response)

    def get_images_from_page(self, response: Response) -> list:
        images = response.css(self.chapter_selector)
        return (
            [self.image_from_element(img).strip() for img in images] if images else []
        )

    def parse_protector_image(self, response: Response) -> list:
        protector_data = self.get_protector_data(response)
        if not protector_data:
            return []

        password = self.get_password_from_protector(protector_data)
        chapter_data_str = self.get_chapter_data_str(protector_data)
        decrypted_text = self.decrypt_chapter_data(chapter_data_str, password)

        return json.loads(decrypted_text)

    def get_protector_data(self, response: Response):
        return response.css(self.chapter_protector_selector).get()

    def get_password_from_protector(self, protector_data: str):
        return re.search(r"wpmangaprotectornonce='(.*?)';", protector_data).group(1)

    def get_chapter_data_str(self, protector_data: str):
        return (
            re.search(r"chapter_data='(.*?)';", protector_data)
            .group(1)
            .replace("\\/", "/")
        )

    def decrypt_chapter_data(self, chapter_data_str: str, password: str):
        chapter_data = json.loads(chapter_data_str)
        salted = b"Salted__"
        salt = bytes.fromhex(chapter_data["s"])
        unsalted_ciphertext = base64.b64decode(chapter_data["ct"])

        ciphertext = salted + salt + unsalted_ciphertext
        decrypted_text = CryptoAES.decrypt(base64.b64encode(ciphertext), password)
        return decrypted_text

    # Extract manga details

    def extract_manga_name_from_home(self, response: Response):
        manga_name = response.css(self.home_manganame_selector).get()
        return manga_name.strip() if manga_name else None

    def extract_cover_from_home(self, response: Response) -> Optional[str]:
        return self.image_from_element(response.css(self.home_cover_selector))

    # extract details from current page

    def extract_manga_details(self, response: Response):
        if self.extract_details_from_script:
            self.extract_details_in_script(response)
        else:
            self.manganame = self.extract_manga_name(response)
            self.cover = self.extract_cover(response)

    def extract_manga_name(self, response: Response):
        return response.xpath(self.manganame_xpath).get().strip()

    def extract_cover(self, response: Response):
        return response.css(self.cover_selector).get()

    def extract_details_in_script(self, response: Response):
        json_ld_data = self.get_json_ld_data(response)
        if json_ld_data:
            self.parse_json_ld_data(json_ld_data)

    def get_json_ld_data(self, response: Response):
        return response.xpath('//script[@type="application/ld+json"]/text()').get()

    def parse_json_ld_data(self, json_ld_data: str):
        try:
            data = json.loads(json_ld_data)
            self.manganame = self.get_manganame_in_json_ld(data)
            self.cover = self.get_cover_in_json_ld(data)
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to decode JSON-LD: {e}")

    def get_cover_in_json_ld(self, data):
        return data.get("image", {}).get("url", self.cover)

    def get_manganame_in_json_ld(self, data):
        return data.get("headline", self.manganame)
