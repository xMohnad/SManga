from SManga.lib.themes.madara import Madara


class AzoramangaSpider(Madara):
    name = "AzoraManga"
    allowed_domains = ["azoramoon.com"]
    base_url = "https://azoramoon.com/"
