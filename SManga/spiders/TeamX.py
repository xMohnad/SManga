from typing import List, Optional

from scrapy.http import Response

from SManga.lib.themes import BaseSpider


class TeamxSpider(BaseSpider):
    name = "TeamX"
    base_url = "https://olympustaff.com/"
    language = "Ara"

    manganame_selector = "div.author-info-title h6::text"

    def extract_next_page_url(self, response: Response):
        return response.css("#next-chapter::attr(href)").get()

    def extract_home_url(self, response: Response):
        return response.css("a.report-chapter::attr(href)").get()

    def extract_title(self, response: Response):
        headingb = response.css("#chapter-heading::text").get(default="").strip()
        chapter_number = response.url.split("/")[-1]
        chapter_title = f"الفصل {chapter_number}"
        return (
            f"{chapter_title} - {headingb}"
            if headingb
            and headingb != chapter_number
            and headingb != f"الفصل رقم {chapter_number}"
            else chapter_title
        )

    def parse_chapter_image(self, response: Response):
        image = response.css("div.page-break img")
        return [self.image_from_element(img).strip() for img in image] if image else []

    # details data

    def extract_manga_name(self, response: Response):
        manga_name = response.css(self.manganame_selector).get()
        return manga_name.strip() if manga_name else None

    def extract_cover(self, response: Response):
        return self.image_from_element(response.css("img.shadow-sm"))

    def extract_description(self, response: Response) -> Optional[str]:
        description = response.css(
            "div.whitebox.shadow-sm div.review-content p::text"
        ).get()
        return description.strip() if description else "الوصف غير متوفر"

    def extract_genre(self, response: Response) -> List[str]:
        genres = response.css("div.review-author-info a.subtitle::text").getall()
        return [genre.strip() for genre in genres if genre.strip()]

    def extract_author(self, response: Response) -> str:
        author = response.css("div:nth-child(10) small:nth-child(2) a::text").get()
        return author.strip() if author else None

    def extract_artist(self, response: Response) -> str:
        return None
