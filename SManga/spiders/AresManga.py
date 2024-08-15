from SManga.lib.themes.mangathemesia import MangaThemesiaSpider


class AresmangaSpider(MangaThemesiaSpider):
    name = "AresManga"
    allowed_domains = ["fl-ares.com"]

    base_url = "https://fl-ares.com/"
    manganame_selector = "#titlemove > h1::text"