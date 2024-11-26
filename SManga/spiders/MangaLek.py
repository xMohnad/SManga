from SManga.lib.themes.madara import Madara


class MangalekSpider(Madara):
    name = "MangaLek"
    base_url = "https://lekmanga.net/"
    language = "Ara"
    selector_manganame = ".c-breadcrumb li:nth-child(2) > a::text"
    home_selector = "ol.breadcrumb li:nth-child(2) > a::attr(href)"

