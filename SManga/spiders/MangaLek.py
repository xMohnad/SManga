from SManga.themes.madara import Madara


class MangalekSpider(Madara):
    name = "MangaLek"
    base_url = "https://lekmanga.net/"
    language = "Ara"
    home_selector = "ol.breadcrumb li:nth-child(2) > a::attr(href)"
