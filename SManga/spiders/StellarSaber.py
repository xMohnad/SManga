from SManga.lib.themes.mangathemesia import MangaThemesiaSpider


class StellarsaberSpider(MangaThemesiaSpider):
    name = "StellarSaber"
    allowed_domains = ["stellarsaber.pro"]
    base_url = "https://stellarsaber.pro/"
