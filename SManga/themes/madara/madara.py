import base64
import json
import re
from typing import List, Optional

from scrapy.http.response import Response

from SManga.lib.cryptoaes import CryptoAES
from SManga.themes import BaseSpider


class Madara(BaseSpider):
    name = ""
    base_url = ""
    language: str = ""

    next_page_selector = ".select-pagination .nav-next a:not(.back)::attr(href)"
    home_selector = "#chapter-heading > a.back::attr(href), ol.breadcrumb li:nth-child(3) > a::attr(href)"
    title_selector = ".c-breadcrumb .active::text"

    chapter_selector = "div.page-break img, li.blocks-gallery-item img, .reading-content .text-left:not(:has(.blocks-gallery-item)) img"
    chapter_protector_selector = "#chapter-protector-data"

    # Manga Details Selector
    selector_manganame = "div.post-title h3, div.post-title h1, #manga-title > h1"
    selector_cover = "div.summary_image img"
    selector_genre = "div.genres-content a::text"
    selector_tag = "div.tags-content::text"
    selector_author = "div.author-content > a::text"
    selector_artist = "div.artist-content > a::text"
    selector_description = (
        "div.description-summary div.summary__content, "
        "div.summary_content div.post-content_item > h5 + div, "
        "div.summary_content div.manga-excerpt, div.manga-summary"
    )

    def extract_next_page_url(self, response: Response) -> Optional[str]:
        return response.css(self.next_page_selector).get(default="").strip()

    def extract_home_url(self, response: Response) -> Optional[str]:
        return response.css(self.home_selector).get()

    def extract_title(self, response: Response) -> str:
        return response.css(self.title_selector).get(default="").strip()

    # Extract chapter images
    def parse_chapter_image(self, response: Response) -> List[str]:
        images = self.get_images_from_page(response)
        return images if images else self.parse_protector_image(response)

    def get_images_from_page(self, response: Response) -> List[str]:
        images = response.css(self.chapter_selector)
        return (
            [self.image_from_element(img).strip() for img in images] if images else []  # pyright: ignore
        )

    def parse_protector_image(self, response: Response) -> List[str]:
        protector_data = self.get_protector_data(response)
        if not protector_data:
            return []

        password = self.get_password_from_protector(protector_data)
        chapter_data_str = self.get_chapter_data_str(protector_data)
        if not chapter_data_str or not password:
            return []

        decrypted_text = self.decrypt_chapter_data(chapter_data_str, password)
        if not decrypted_text:
            return []

        return json.loads(json.loads(decrypted_text))

    def get_protector_data(self, response: Response) -> Optional[str]:
        return response.css(self.chapter_protector_selector).get()

    def get_password_from_protector(self, protector_data: str) -> Optional[str]:
        match = re.search(r"wpmangaprotectornonce='(.*?)';", protector_data)
        return match.group(1) if match else None

    def get_chapter_data_str(self, protector_data: str) -> Optional[str]:
        match = re.search(r"chapter_data='(.*?)';", protector_data)
        return match.group(1).replace("\\/", "/") if match else None

    def decrypt_chapter_data(
        self, chapter_data_str: str, password: str
    ) -> Optional[str]:
        try:
            chapter_data = json.loads(chapter_data_str)
            salted = b"Salted__"
            salt = bytes.fromhex(chapter_data["s"])
            unsalted_ciphertext = base64.b64decode(chapter_data["ct"])

            ciphertext = salted + salt + unsalted_ciphertext
            decrypted_text = CryptoAES.decrypt(base64.b64encode(ciphertext), password)
            return decrypted_text
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"Error decrypting chapter data: {e}")
            return None

    # Extract manga details
    def extract_manga_name(self, response: Response) -> str:
        return (
            response.css(self.selector_manganame)
            .xpath(".//text()")
            .get(default="UnknownManga")
            .strip()
        )

    def extract_cover(self, response: Response) -> Optional[str]:
        cover_element = response.css(self.selector_cover)
        return self.image_from_element(cover_element) if cover_element else None

    def extract_description(self, response: Response) -> Optional[str]:
        element = response.css(self.selector_description)
        if element.css("p::text").getall():
            description = "\n\n".join(
                p.get().replace("<br>", "\n").strip() for p in element.css("p::text")
            )
        else:
            description = element.xpath(".//text()").get(default="").strip()

        return description if description else None

    def extract_genre(self, response: Response) -> List[str]:
        genres = [
            *response.css(self.selector_genre).getall(),
            response.css(self.selector_tag).get(),
        ]
        return [genre.strip() for genre in genres if genre and genre.strip()]

    def extract_author(self, response: Response) -> Optional[str]:
        author = response.css(self.selector_author).get()
        return author.strip() if author else None

    def extract_artist(self, response: Response) -> Optional[str]:
        artist = response.css(self.selector_artist).get()
        return artist.strip() if artist else None
