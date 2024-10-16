from scrapy.http import Response
from SManga.lib.themes import BaseSpider

class TeamxSpider(BaseSpider):
    name = "TeamX"
    base_url = "https://teamoney.site/"
    language = "Ara"
    extract_details_from_current_page = False

    manganame_selector = "div.author-info-title h6::text"

    def extract_next_page_url(self, response: Response):
        return response.css("#next-chapter::attr(href)").get()

    def extract_home_url(self, response: Response):
        return response.css("a.report-chapter::attr(href)").get()

    def extract_title(self, response: Response):
        headingb = response.css("#chapter-heading::text").get().strip()
        chapter_number = response.url.split("/")[-1]
        return (
            f"الفصل {chapter_number} - {headingb}"
            if headingb and headingb != chapter_number
            else f"الفصل {chapter_number}"
        )

    def parse_chapter_image(self, response: Response):
        image = response.css("div.page-break img")
        return [self.image_from_element(img).strip() for img in image] if image else []

    def extract_manga_name_from_home(self, response: Response):
        manga_name = response.css(self.manganame_selector).get()
        return manga_name.strip() if manga_name else None

    def extract_cover_from_home(self, response: Response):
        return self.image_from_element(response.css("img.shadow-sm"))
