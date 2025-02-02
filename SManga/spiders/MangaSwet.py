from SManga.themes.mangathemesia import MangaThemesiaSpider


class MangaswetSpider(MangaThemesiaSpider):
    name = "MangaSwet"
    base_url = "https://swatscans.com/"
    language = "Ara"

    series_artist_selector = "span:contains(الناشر) i"
    series_author_selector = "span:contains(المؤلف) i"
