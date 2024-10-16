from SManga.lib.themes.madara import Madara


class MangalekSpider(Madara):
    name = "MangaLek"
    base_url = "https://lekmanga.net/"
    language = "Ara"
    manganame_selector = ".c-breadcrumb li:nth-child(2) > a::text"
