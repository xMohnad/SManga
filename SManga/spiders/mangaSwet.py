from SManga.lib.themes.mangathemesia import MangaThemesiaSpider


class MangaswetSpider(MangaThemesiaSpider):
    name = "MangaSwet"
    allowed_domains = ["tatwt.com"]
    base_url = "https://tatwt.com/"
