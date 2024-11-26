import json
import base64
from typing import List, Optional
from scrapy.http import Response
from scrapy.selector import Selector


from SManga.lib.themes import BaseSpider
from SManga.items import MangaDetails

# selector_manganame = "div.infox > h1"

class MangaThemesiaSpider(BaseSpider):
    name = ""
    base_url = ""
    language: str = ""

    title_selector = "div.headpost > h1::text"
    home_page_selector = "div.headpost > div > a::attr(href)"

    script_xpath = "//script[contains(text(),'ts_reader')]//text()"
    script_base64_xpath = '//script[starts-with(@src, "data:text/javascript;base64,dHNfcmVhZGVyLnJ1bih7")]'
    
    def extract_title(self, response: Response) -> str:
        title = response.css(self.title_selector).get()
        return title.split("–")[-1].strip() if title else "UnknownChapter"

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

    ## Selectors
    series_details_selector = "div.bigcontent, div.animefull, div.main-info, div.postbody"
   
    series_cover_selector = ".infomanga > div[itemprop=image] img, .thumb img"
    series_manga_name_selector = "h1.entry-title, .ts-breadcrumb li:last-child span, h1[itemprop=headline]"
   
    @staticmethod
    def selector(selector, contains):
        return ", ".join(selector.replace("%s", term) for term in contains)

    series_author_selector = selector(
        ".infotable tr:contains(%s) td:last-child, .tsinfo .imptdt:contains(%s) i, .fmed b:contains(%s)+span, span:contains(%s) ",
        ["Author", "Auteur", "autor", "المؤلف", "Mangaka", "seniman", "Pengarang", "Yazar"]
    )

    series_artist_selector = selector(
        ".infotable tr:contains(%s) td:last-child, .tsinfo .imptdt:contains(%s) i, .fmed b:contains(%s)+span, span:contains(%s) ",
        ["Artist", "Artiste", "Artista", "الرسام", "الناشر", "İllüstratör", "Çizer"]
    )
    
    series_description_selector = ".desc, .entry-content[itemprop=description]"

    series_alt_name_selector = (
        ".alternative, .wd-full:contains(alt) span, .alter, .seriestualt, " +
        selector(
            ".infotable tr:contains(%s) td:last-child",
            ["Alternative", "Alternatif", "'الأسماء الثانوية'"]
        )
    )

    series_genre_selector = (
        "div.gnr a, .mgen a, .seriestugenre a, " +
        selector(
            "span:contains(%s)",
            ["genre", "التصنيف"]
        )
    )

    series_type_selector = (
        selector(
            ".infotable tr:contains(%s) td:last-child, .tsinfo .imptdt:contains(%s) i, "
            ".tsinfo .imptdt:contains(%s) a, .fmed b:contains(%s)+span, span:contains(%s) a",
            ["type", "ประเภท", "النوع", "tipe", "Türü"]
        ) + ", a[href*=type\\=]"
    )

    alt_name_prefix = "Alternative Names: "
    
    def get_details_and_retry(self, response: Response):
        details = response.css(self.series_details_selector)
        item = MangaDetails()
        item["source"] = self.name
        
        if details:
            item["manganame"] = self.clean_text(details.css(self.series_manga_name_selector))
            item["cover"] = self.image_from_element(response.css(self.series_cover_selector))

            description = self.clean_text(details.css(self.series_description_selector), True)
            alt_name = self.clean_text(details.css(self.series_alt_name_selector), True)
            if alt_name:
                description = f"{description}\n\n{self.alt_name_prefix}{alt_name}".strip()

            genres = self.clean_text(details.css(self.series_genre_selector), True, None) 
            series_type = self.clean_text(details.css(self.series_type_selector))
            if series_type:
                genres.append(series_type)
            genres = [genre.capitalize() for genre in genres if genre]

            item["description"] = description
            item["genre"] = genres
            item["author"] = self.clean_text(details.css(self.series_author_selector))
            item["artist"] = self.clean_text(details.css(self.series_artist_selector))

        retry_url = response.meta.get("retry")
        if retry_url:
            yield response.follow(
                url=retry_url,
                callback=self.parse,
                meta={"details_item": item},
                dont_filter=True,
            )

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
