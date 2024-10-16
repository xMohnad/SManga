from SManga.lib.themes.mangathemesia import MangaThemesiaSpider


class AresmangaSpider(MangaThemesiaSpider):
    name = "AresManga"
    base_url = "https://fl-ares.com/"
    language = "Ara"
    
    manganame_selector = "#titlemove > h1::text"
